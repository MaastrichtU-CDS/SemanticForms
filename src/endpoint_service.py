from SPARQLWrapper import SPARQLWrapper, POST, DIGEST, JSON
import requests
import logging
import sys

class SPARQLEndpoint:
    def __init__(self, server_url, repository_name, update_endpoint_suffix=None):
        """
        The SPARQLEndpoint class manages communication to the SPARQL endpoint.
        sparql_url: the SPARQL endpoint URL
        sparqlUpdateUrl: optional, if the endpoint uses a separate update url, provide this URL here
        """
        self.__sparql_url = server_url + "/repositories/" + repository_name
        self.__sparql_update_url = self.__sparql_url
        if update_endpoint_suffix is not None:
            self.__sparql_update_url = self.__sparql_update_url + update_endpoint_suffix
        
        repo_exists = self.__create_repo_if_not_exists(server_url, repository_name)
        if not repo_exists:
            print(f"Cannot create or find RDF endpoint {self.__sparql_url}")
            sys.exit(9)

    def __create_repo_if_not_exists(self, server_url, repository_name):
        url = server_url + "/repositories"
        response = requests.get(url, headers={"Accept": "application/sparql-results+json"})

        repositories = response.json()["results"]["bindings"]
        for repository in repositories:
            print(repository["id"]["value"] + " | " + repository_name)
            if repository["id"]["value"] == repository_name:
                return True
        
        print("repository not found, attempting to create")
        url = server_url + "/rest/repositories"
        repoConfig = f"""
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix rep: <http://www.openrdf.org/config/repository#> .
            @prefix sail: <http://www.openrdf.org/config/sail#> .
            @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

            <#{repository_name}> a rep:Repository;
            rep:repositoryID "{repository_name}";
            rep:repositoryImpl [
                rep:repositoryType "graphdb:FreeSailRepository";
                <http://www.openrdf.org/config/repository/sail#sailImpl> [
                    <http://www.ontotext.com/trree/owlim#base-URL> "http://example.org/owlim#";
                    <http://www.ontotext.com/trree/owlim#check-for-inconsistencies> "false";
                    <http://www.ontotext.com/trree/owlim#defaultNS> "";
                    <http://www.ontotext.com/trree/owlim#disable-sameAs> "true";
                    <http://www.ontotext.com/trree/owlim#enable-context-index> "false";
                    <http://www.ontotext.com/trree/owlim#enable-literal-index> "true";
                    <http://www.ontotext.com/trree/owlim#enablePredicateList> "true";
                    <http://www.ontotext.com/trree/owlim#entity-id-size> "32";
                    <http://www.ontotext.com/trree/owlim#entity-index-size> "10000000";
                    <http://www.ontotext.com/trree/owlim#imports> "";
                    <http://www.ontotext.com/trree/owlim#in-memory-literal-properties> "true";
                    <http://www.ontotext.com/trree/owlim#query-limit-results> "0";
                    <http://www.ontotext.com/trree/owlim#query-timeout> "0";
                    <http://www.ontotext.com/trree/owlim#read-only> "false";
                    <http://www.ontotext.com/trree/owlim#repository-type> "file-repository";
                    <http://www.ontotext.com/trree/owlim#ruleset> "empty";
                    <http://www.ontotext.com/trree/owlim#storage-folder> "storage";
                    <http://www.ontotext.com/trree/owlim#throw-QueryEvaluationException-on-timeout> "false";
                    sail:sailType "graphdb:FreeSail"
                    ]
                ];
            rdfs:label "{repository_name}" .
        """
        data = { "config": repoConfig }
        # header = { "Content-Type": "multipart/form-data" }
        response = requests.post(url, files=data)#, headers=header)
        if response.status_code >= 200 & response.status_code < 300:
            return True
    
        return False

    def list_instances(self, titlePredicate=None):
        """
        Retrieve all instances stored in the SPARQL endpoint
        Input parameters:
          - titlePredicate: Full URL path of the predicate URI to use (DataProperty).
        """
        
        if titlePredicate is None:
            titlePredicate = "rdfs:label"
        
        predicateInsert = "OPTIONAL { ?instance <"+titlePredicate+"> ?title. }"

        query = """
        prefix pav: <http://purl.org/pav/>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        select distinct ?instance ?time ?title
        where { 
            ?instance pav:createdOn ?time.
        """
        query += predicateInsert
        query += """
        }
        """

        print(query)
        sparql = SPARQLWrapper(self.__sparql_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return results["results"]["bindings"]
    
    def describe_instance(self, instance_uri):
        """
        Retrieve the direct properties of the given instance
        """
        sparql = SPARQLWrapper(self.__sparql_url)
        sparql.setQuery("""
        SELECT ?predicate ?predicate_label ?object ?object_label
        WHERE {
            <%s> ?predicate ?object.
            OPTIONAL { ?predicate rdfs:label ?predicate_label }.
            OPTIONAL { ?object rdfs:label ?object_label }.
        }
        """ % instance_uri)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return results["results"]["bindings"]
    
    def get_instance_links(self, instance_uri):
        """
        Retrieve the references of this instance
        """
        sparql = SPARQLWrapper(self.__sparql_url)
        sparql.setQuery("""
        SELECT ?predicate ?object
        WHERE {
            ?subject ?predicate <%s>.
        }
        """ % instance_uri)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return results["results"]["bindings"]

    def drop_instance(self, identifier):
        """
        Delete the form instance
        """
        query = "DROP GRAPH <%s>" % identifier
        sparql = SPARQLWrapper(self.__sparql_update_url)
        sparql.setMethod(POST)
        sparql.setQuery(query)

        logging.debug(query)

        results = sparql.query()
        logging.debug(results.response.read())

    def store_instance(self, rdf_string, graph_uri=None):
        """
        Store data to a SPARQL endpoint.
        rdf_string: containing the triples (format=nt) to store
        graph_uri: optional, to set the named graph
        """
        queryData = "INSERT DATA { %s }" % rdf_string
        if graph_uri is not None:
            queryData = "INSERT DATA { GRAPH <%s> { %s } }" % (graph_uri, rdf_string)

        sparql = SPARQLWrapper(self.__sparql_update_url)
        sparql.setMethod(POST)
        sparql.setQuery(queryData)

        logging.debug(f"Storing data to endpoint {self.__sparql_update_url}")
        logging.debug(queryData)

        results = sparql.query()
        logging.debug(results.response.read())