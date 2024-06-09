import os, json

class Persistance:
    def __init__(self):
        print("Initializing persistance")

class FilePersistance(Persistance):
    def __init__(self, folder_location: str, title_uri: str, base_url='http://localhost/template-instances'):
        Persistance.__init__(self)
        self.__folder_location = folder_location
        self.__title_uri = title_uri
        self.__base_url = base_url
        self.__cached_items = { }
        self.__create_folder_if_not_exists()
        self.__scan_folder(action=self.__parse_jsonld_file)
    
    def __create_folder_if_not_exists(self):
        """
        Create the persistance folder if it does not exist.
        """
        if not os.path.exists(self.__folder_location):
            os.makedirs(self.__folder_location)
    
    def __scan_folder(self, action):
        """
        Loop over folders and detect files which are .jsonld files. In that specific case, execute the passed function
        """
        self.__cached_items = { }
        for root, dirs, files in os.walk(self.__folder_location, topdown=True):
            for myFile in files:
                if myFile.endswith(".jsonld"):
                    action(filename=os.path.join(root, myFile))
    
    def __parse_jsonld_file(self, filename: str):
        """
        Read JSON-LD object from filename, and parse the title and identifier of the object.
        input:
            - filename: the path of the file to parse
        """
        with open(filename, 'r') as f:
            metadata = json.load(f)
            id = metadata["@id"].replace(self.__base_url + "/", "")
            titleTag = None
            print(metadata["@context"])
            for key in metadata["@context"]:
                value = metadata["@context"][key]
                if value == self.__title_uri:
                    titleTag = key
            
            self.__cached_items[id] = {
                "title": metadata[titleTag]['@value'],
                "filename": filename,
                "time": metadata['pav:createdOn']
            }
    
    def list_instances(self):
        return self.__cached_items.copy()