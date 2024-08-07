import streamlit as st
import time

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

es_client = Elasticsearch('http://localhost:9200')

#default
#index_name_global='podcasts_multi-qa-minilm-l6-cos-v1__dims_384' 
#model_name = 'multi-qa-MiniLM-L6-cos-v1'
#model_embed = SentenceTransformer(model_name)

def elastic_search(query, index_name = 'podcasts_multi-qa-minilm-l6-cos-v1__dims_384'):
    search_query = {
        "size": 3,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["description^3", "name"],
                        "type": "best_fields"
                    }
                }
            }
        }
    }

    response = es_client.search(index=index_name, body=search_query)
    
    result_docs = []
    
    for hit in response['hits']['hits']:
        result_docs.append(hit['_source'])
    
    return result_docs

def elastic_search_knn(field, vector,index_name):
    knn = {
        "field": field,
        "query_vector": vector,
        "k": 3,
        "num_candidates": 10000,
    }

    search_query = {
        "knn": knn,
        "_source": ["description","name","category","url"]
    }

    es_results = es_client.search(
        index=index_name_global,
        body=search_query
    )
    
    result_docs = []
    
    for hit in es_results['hits']['hits']:
        result_docs.append(hit['_source'])

    return result_docs

def description_vector_knn(query,model_embed,index_name):
    print("index_name",index_name)

    v_q = model_embed.encode(query)
    return elastic_search_knn('description_vector', v_q, index_name)


def recommend_docs_to_text(result_docs):
    for doc in result_docs:
        st.header(doc['name'])
        st.subheader("Category: "+doc['category'])
        st.write(doc['description'])
        st.write("[link](%s)" % doc['url'])
        


siteHeader = st.container()
searchExploration = st.container()

with siteHeader:
    st.title('Podcast Recommendation System')
    st.markdown("by :red[**Anastasia**] :computer:")

with searchExploration:
    user_choice = st.selectbox('**How would you like to get podcast recommendations?**',
       options = ('Select an option.....','Key-based search', 'Semantic Search'))

    if user_choice == 'Key-based search':
        podcast_keywords_from_user = st.text_input('**Enter keywords**')
        keybased_recommendations = elastic_search(podcast_keywords_from_user)
        st.write(recommend_docs_to_text(keybased_recommendations))
    if user_choice == 'Semantic Search':
        selected_model = st.radio(
            "Select the model",
            ["***multi-qa-mpnet-base-dot-v1***", "***multi-qa-MiniLM-L6-cos-v1***", ":rainbow[multi-qa-distilbert-cos-v1]"],
            captions=[
                "Big and slow",
                "Small and quick",
                "Best Search performance"
            ],
        )
        st.write("[read more about models](%s)" % 'https://sbert.net/docs/sentence_transformer/pretrained_models.html')

        st.write("You selected:", selected_model)
        index_name_global = ''
        model_name = ''
        model_embed = None
        if selected_model == "***multi-qa-mpnet-base-dot-v1***":
            index_name_global='podcasts_multi-qa-mpnet-base-dot-v1__dims_768' 
            model_name = 'multi-qa-mpnet-base-dot-v1'
            model_embed = SentenceTransformer(model_name)

        if selected_model == "***multi-qa-MiniLM-L6-cos-v1***":
            index_name_global='podcasts_multi-qa-minilm-l6-cos-v1__dims_384' 
            model_name = 'multi-qa-MiniLM-L6-cos-v1'
            model_embed = SentenceTransformer(model_name)
    
        if selected_model == ":rainbow[multi-qa-distilbert-cos-v1]":
            index_name_global= 'podcasts_multi-qa-distilbert-cos-v1__dims_768' 
            model_name = 'multi-qa-distilbert-cos-v1'
            model_embed = SentenceTransformer(model_name)

        print(len(model_embed.encode("This is a simple sentence")))

        podcast_keywords_from_user = st.text_input('**Enter description**')
        keybased_recommendations = description_vector_knn(podcast_keywords_from_user,model_embed=model_embed,index_name=index_name_global)
        st.write(recommend_docs_to_text(keybased_recommendations))