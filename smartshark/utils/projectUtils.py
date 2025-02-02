import pygit2
import os
import shutil
import datetime

from smartshark.mongohandler import handler


def getPlugins():
    # Load the tables directly from the MongoDB
    schemas = {}
    query = handler.client.get_database(handler.database).get_collection('plugin_schema').find()

    plugins = {}
    for schema in query:
        name, version = schema["plugin"].split('_')
        version = version.split('.')  # Split into tuple
        if name in plugins:
            if version > plugins[name]:
                schemas[name] = schema

        else:
            schemas[name] = schema
            plugins[name] = version

    # Alternativ way to get the schema via the files of the plugin installations
    # for root, dirs, files in os.walk(plugin_path):
    #    for name in files:
    #        if name == 'schema.json':
    #            filepath = os.path.join(root, name)
    #            json1_file = open(filepath).read()
    #            json_data = json.loads(json1_file)
    #            schemas.append(json_data)
    return schemas


def findDependencyOfSchema(name, schemas, ground_dependencys=[]):
    dependencys = []
    for schema in schemas:
        for collection in schema['collections']:
            # For each field in the collection check if the field is a reference
            if(collection['collection_name'] not in ground_dependencys):
                for field in collection['fields']:
                    if('reference_to' in field and field['reference_to'] == name):
                        ground_dependencys.append(collection['collection_name'])
                        dependencys.append(SchemaReference(collection['collection_name'],field['field_name'], findDependencyOfSchema(collection['collection_name'],schemas, ground_dependencys)))

    return dependencys


def count_on_dependency_tree(tree, parent_id):

    ids = handler.client.get_database(handler.database).get_collection(tree.collection_name).find({tree.field: parent_id}).distinct('_id')
    count = len(ids)
    tree.count = tree.count + count
    i=0
    for _id in ids:
        if i%1000==0:
            if tree.collection_name=='commit':
                print("commits done: %i / %i" % (i, count))
        i=i+1
        for deb in tree.dependencys:
            count_on_dependency_tree(deb, _id)


def delete_on_dependency_tree(tree, parent_id):

    ids = handler.client.get_database(handler.database).get_collection(tree.collection_name).find({tree.field: parent_id}).distinct('_id')
    count = len(ids)

    tree.count = tree.count + count
    i=0
    for _id in ids:
        if i%1000==0:
            if tree.collection_name=='commit':
                print("commits done: %i / %i" % (i, count))
        i=i+1
        for deb in tree.dependencys:
            delete_on_dependency_tree(deb, _id)

    handler.client.get_database(handler.database).get_collection(tree.collection_name).delete_many({tree.field: parent_id})


def create_local_repo_for_project(vcsMongo, path, project_name):
    url = vcsMongo["url"]
    # removes the https and replaces it with git
    repo_url = "git" + url[5:]
    # if os.path.isdir(path):
    #     shutil.rmtree(path)

    # check if we have the project file locally (HPC SYSTEM ONLY!)
    hpc_path = '/mnt/jgrabow1/bin/projects/{}'.format(project_name)
    if os.path.isdir(hpc_path):
        # shutil.copytree(hpc_path, path)
        # workaround because our tmpdir path exists already, adopted from: https://stackoverflow.com/a/12514470
        for item in os.listdir(hpc_path):
            s = os.path.join(hpc_path, item)
            d = os.path.join(path, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # complete path
        if not path.endswith('.git'):
            if not path.endswith('/'):
                path += '/'
            path += '.git'
        repo = pygit2.Repository(path)
    else:
        repo = pygit2.clone_repository(repo_url, path)
        # this is a workaround for: https://github.com/libgit2/pygit2/issues/818
        repo = pygit2.Repository(path)

    return repo


def get_all_commits_of_repo(vcsMongo, repo):
    total_commit_hexs = []

    walk_objects = []

    # first get all possible branches
    for branch in repo.branches:
        if type(branch) == str:
            walk_objects.append(repo.branches[branch])

    # then we need tags in cases those are not on any branch (this really happens!)
    for obj in repo:
        if repo[obj].type == pygit2.GIT_OBJ_TAG:
            walk_objects.append(repo[obj])

    for obj in walk_objects:
        for commit in repo.walk(obj.target, pygit2.GIT_SORT_TIME):
            if commit.hex not in total_commit_hexs:
                time = datetime.datetime.utcfromtimestamp(commit.commit_time)
                if time < vcsMongo["last_updated"]:
                    total_commit_hexs.append(commit.hex)

    return total_commit_hexs


class SchemaReference:

    def __init__(self, collection_name, field, deb):
        self.collection_name = collection_name
        self.field = field
        self.dependencys = deb
        self.count = 0

    def __repr__(self):
        return str(self.collection_name) + " --> " + str(self.field) + " Dependencys:" + str(self.dependencys)

    def __str__(self):
        return str(self.collection_name) + " --> " + str(self.field) + " Dependencys:" + str(self.dependencys)


def get_commit_from_database(db, commitHex, vcs_system_id):
    return db.commit.find_one({"revision_hash": commitHex, 'vcs_system_id': vcs_system_id})


def get_code_entities_from_database(db, db_commit, use_meme):
    if use_meme:
        try:
            list_of_ids = db_commit["code_entity_states"]
            return db.code_entity_state.find({"_id": {"$in": list_of_ids}})
        except KeyError:
            # this can happen on commits without code_entity_states (i.e. only non-code files)
            return []
    else:
        return db.code_entity_state.find({"commit_id": db_commit['_id']})
