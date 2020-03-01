'''
A class "clustering" which uses
saved TFIDF and Clustering models
for giving predictions about new scripts.

In functions for prediction, an argument "preprocess"
is provided. Make it true while calling the function, and
the code will extract keywords from the input script first.
While, if the input script is already represented as extracted
keywords, make preprocess arg False.

Possible predictions:
(i) noncritical (ii) critical (iii) translateable
'''
import pickle
from collections import OrderedDict
import re

class clustering:
    def __init__(self, tfidf_model, clustering_model, final_features):
        '''
        initiazes class object by loading saved models
        from files whose names are provided as arguments.
        It also makes js_features_dict as it might need to
        extract keywords from the scripts
        '''
        self.vectorizer = pickle.load(open(tfidf_model, "rb"))
        self.predictor = pickle.load(open(clustering_model, "rb"))
        self.js_features_dict = OrderedDict()
        with open(final_features, 'r') as ref:
            for line in ref:
                if '|' in line:
                    words = line.strip().split('|')
                    self.js_features_dict[words[0]] = words[1]

    def readable(self, x):
        '''
        In the files "tf_model.sav" and "cl_model.sav",
        the stored models are such that the cluster 0
        gets dominated by rule based class 0, and cluster 1
        get dominated by rule based class 1, and so on.
        Therefore, label 0 can be directly converted to
        non-critical, 1 to critical and 2 to replaceable
        '''
        if x == 0:
            return "non-critical"
        if x == 1:
            return "critical"
        if x == 2:
            return "replaceable"
        return x

    def extract_keywords(self, scripts):
        '''
        Extract keywords from the provided
        scripts.
        '''
        res = []
        for script in scripts:
            # converts multiple contiguous spaces to a single space
            content = re.sub(' +', ' ', script)
            kws = []
            for feature in self.js_features_dict:
                count = content.count(
                    "."+feature+"(") + content.count("."+feature+" (")
                if count:
                    kws += ([feature]*count)
            res += [" ".join(kws)]
        return res

    def batch_predict(self, scripts, preprocess):
        '''
        if preprocess is True: keywords will be extracted from
        the scripts first and then model will be run. If it is false,
        it is assumed that scripts are already in the keywords form.

        Takes a list of documents as an argument.
        Returns a list of predictions ordered by the
        order of documents in the input list
        '''

        if preprocess:
            scripts = self.extract_keywords(scripts)
        else:
            scripts = [" ".join(x) for x in scripts]
        X = self.vectorizer.transform(scripts).toarray()
        preds = self.predictor.predict(X)
        res = list(map(lambda x: self.readable(x), preds))
        return res

    def predict(self, script, preprocess):
        '''
        if preprocess is True: keywords will be extracted from
        the scripts first and then model will be run. If it is false,
        it is assumed that scripts are already in the keywords form.

        Takes a single script which is "string", as an argument
        and returns corresponding label which is also
        "string"
        '''
        res = ""
        if preprocess:
            res = self.batch_predict([script], preprocess)
        else:
            if not isinstance(script, list):
                raise Exception(
                    "When preprocess is False, a list of keywords should be provided.")
            res = self.batch_predict(script, preprocess)
        return res[0]
