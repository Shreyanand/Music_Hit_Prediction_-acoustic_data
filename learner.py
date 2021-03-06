# -*- coding: utf-8 -*-
"""
Created on Tue Apr 10 15:18:39 2018

@author: suvod
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 12:07:05 2018

@author: suvod
"""

import os
import pandas as pd
from sklearn import svm
from sklearn.naive_bayes import MultinomialNB,GaussianNB,BernoulliNB
from sklearn.neural_network import MLPClassifier
from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn import model_selection
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
import neural_network
import smote
from sklearn.ensemble import AdaBoostClassifier
import numpy as np 
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.cross_validation import StratifiedKFold
from sklearn.metrics import roc_curve, auc, roc_auc_score
import matplotlib.pyplot as plt
from scipy import interp

import nb


class learner():
    
    def __init__(self,fold):
        self.data_X = None
        self.data_y = None
        self.doSmt = False
        self.clf = None
        self.data_loc = "data"
        self.class_s = "<"
        self.class_label = None
        self.model = None
        self.cwd = os.getcwd()
        self.data_path = os.path.join(self.cwd, self.data_loc)
        self.file_path = os.path.join(self.data_path, "processed_data.pkl")
        self.data = pd.read_pickle(self.file_path)
        self.preserved_data = pd.read_pickle(self.file_path)
        self.headers = self.data.columns.values.tolist()
        for __header in self.headers:
             if self.class_s in __header:
                self.class_label = __header
        self.columns = self.data.columns.values.tolist()
        self.data_y = self.data[self.class_label]
        self.data.drop([self.class_label], axis=1, inplace = True)
        self.data_X = self.data
        self.fold = fold
        self.result = []
        self.roc_results = []
        self.tprs = []
        self.aucs = []
        self.mean_fpr = np.linspace(0, 1, 100)

    def train(self, model):
        print("Model training Starting>>>>>>>>>>>>")
        print("Starting with Model ", model)
        self.selectedLearner(model)
        kf = StratifiedKFold(self.data_y.values, self.fold, shuffle=True)
        for train_index, test_index in kf:
            self.train_X = self.data_X.ix[train_index]
            self.test_X = self.data_X.ix[test_index]
            self.train_y = self.data_y.ix[train_index]
            self.test_y = self.data_y[test_index]
            if self.doSmt:
                self.doSmote()
            if model == 'NBO':
                self.clf.set_data(self.preserved_data,self.train_X,self.train_y,self.test_X,self.test_y)
                predict = self.clf.nb_fit_predict()
                print(metrics.classification_report(self.test_y, predict, digits=3))
                print(metrics.confusion_matrix(self.test_y, predict))
                res =  [metrics.f1_score(self.test_y, predict,average='weighted'),
                        metrics.accuracy_score(self.test_y, predict), metrics.roc_auc_score(self.test_y, self.clf.predict_proba(np.array(self.test_X))[:,1], average='weighted')]
                pred_prob = self.clf.predict_proba(np.array(self.test_X))[:,1]
                self.tprs, self.aucs = self.compute_roc(self.clf, self.train_X, self.train_y, self.test_X, self.test_y, pred_prob)
                
            elif model == 'NBL2':
                res, predict, y = self.model.fit_predict(self.clf, self.train_X, self.train_y, self.test_X, self.test_y, self.class_label)
                roc = np.array(roc_curve(y, predict))
                self.roc_results.append(roc)
                
            elif model == 'NBL3':
                res, predict, y = self.model.fit_predict(self.clf, self.train_X, self.train_y, self.test_X, self.test_y, self.class_label)
                roc = np.array(roc_curve(y, predict))
                self.roc_results.append(roc)
                
            elif model == 'NN':
                self.clf.fit(np.array(self.train_X), np.array(self.train_y), 10, 100000, True)
                predict = self.clf.predict(np.array(self.test_X))
                print(metrics.classification_report(self.test_y, predict, digits=3))
                print(metrics.confusion_matrix(self.test_y, predict))
                res =  [metrics.f1_score(self.test_y, predict,average='weighted'),
                        metrics.accuracy_score(self.test_y, predict),metrics.roc_auc_score(self.test_y, predict, average='weighted')]
                roc = np.array(roc_curve(self.test_y, predict))
                self.roc_results.append(roc)
                
            else:
                self.clf.fit(self.train_X, self.train_y)
                predict = self.clf.predict(self.test_X)
                print(metrics.classification_report(self.test_y, predict, digits=3))
                print(metrics.confusion_matrix(self.test_y, predict))
                res = [metrics.f1_score(self.test_y, predict,average='weighted'),
                       metrics.accuracy_score(self.test_y, predict),metrics.roc_auc_score(self.test_y, self.clf.predict_proba(np.array(self.test_X))[:,1], average='weighted')]
                pred_prob = self.clf.predict_proba(np.array(self.test_X))[:,1]
                self.tprs, self.aucs = self.compute_roc(self.clf, self.train_X, self.train_y, self.test_X, self.test_y, pred_prob)
               
            self.result.append(res)
            
        self.result = pd.DataFrame(self.result, columns = ['f1-score','Accuracy','AUC'])
        self.result = self.result.mean()
        
        if(model == 'NBL2' or model == 'NBL3' or model == 'NN'):
            self.roc_results = np.divide(np.array(self.roc_results).sum(axis=0),self.fold)
            self.plot_roc(self.roc_results, self.result['AUC'], model)
        else:
            self.plot_roc_2(self.tprs, self.aucs, model)
        
        return self.result
    
    
    def selectedLearner(self, model):
        if model == 'DT':
            print("Decision Tree Training")
            self.clf = tree.DecisionTreeClassifier(criterion='entropy')
        elif model == 'RF':
            print("Random Forest Tree Training")
            self.clf = RandomForestClassifier(n_estimators=2000, criterion='entropy')
        elif model == 'SVM':
            print("SVM Training")
            self.clf = svm.SVC(kernel='linear', probability=True)
        elif model == 'LR':
            print("Logistic Regression Training")
            self.clf = LogisticRegression()
        elif model == 'NB':
            print("Naive Bayes Training")
            self.clf = GaussianNB()
        elif model == 'MLP':
            print("Neural Network Training")
            self.clf = MLPClassifier(hidden_layer_sizes=500, activation='tanh', learning_rate='adaptive', max_iter=15000)
        elif model == 'NN':
            print("Our Neural Network Training")
            self.clf = neural_network.NNClassifier()
        elif model == 'ADA':
            print("AdaBoost Training")
            self.clf = AdaBoostClassifier()
        elif model == 'KNN':
            print("KNN Training")
            self.clf = KNeighborsClassifier(n_neighbors=10)
        elif model == 'NBL2':
            print("NBL2 model Training")
            self.model = NBL2()
            self.clf = GaussianNB()
        elif model == 'NBL3':
            print("NBL2 model Training")
            self.model = NBL3()
            self.clf = GaussianNB()
        elif model == 'NBO':
            print("Our implementation of NB is running")
            self.clf = nb.naive_bayes()
        return self.clf

    def doSmote(self):
        df = pd.concat([self.train_X, self.train_y], axis=1)
        columnNames = self.data.columns.values.tolist()
        columnNames.append(self.class_label)
        smt = smote.smote(df, 5)
        self.data = smt.fit_transform()
        self.data.columns = columnNames
        self.train_y = self.data[self.class_label]
        self.data.drop([self.class_label], axis=1, inplace=True)
        self.train_X = self.data
        
        
    def compute_roc(self, clf, train_X, train_y, test_X, test_y, probas_):
        
        fpr, tpr, thresholds = roc_curve(test_y, probas_)
        self.tprs.append(interp(self.mean_fpr, fpr, tpr))
        self.tprs[-1][0] = 0.0
        roc_auc = auc(fpr, tpr)
        self.aucs.append(roc_auc)
        
        return self.tprs, self.aucs  
        
    def plot_roc_2(self, tprs, aucs, model):
        
        plt.plot([0, 1], [0, 1], linestyle='--', lw=2, color='r',
                 label='Luck', alpha=.8)
        
        mean_tpr = np.mean(tprs, axis=0)
        mean_tpr[-1] = 1.0
        mean_auc = auc(self.mean_fpr, mean_tpr)
    
        std_auc = np.std(aucs)
        plt.plot(self.mean_fpr, mean_tpr, color='b',
                 label= str(model)+' (AUC = %0.2f $\pm$ %0.2f)' % (mean_auc, std_auc),
                 lw=2, alpha=.8)
        
        std_tpr = np.std(tprs, axis=0)
        tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
        tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
        plt.fill_between(self.mean_fpr, tprs_lower, tprs_upper, color='grey', alpha=.2,
                         label=r'$\pm$ 1 std. dev.')
        
        plt.xlim([-0.05, 1.05])
        plt.ylim([-0.05, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic example')
        plt.legend(loc="lower right")
        plt.show()
        
        
    def plot_roc(self, roc_results, rocauc, model):
        
        fpr, tpr, thr = roc_results[0], roc_results[1], roc_results[2] 
    
        plt.plot([0, 1], [0, 1], linestyle='--', lw=2, color='r',
                 label='Luck', alpha=.8)
        
        plt.plot(fpr, tpr, color='b',
                 label= str(model)+' (AUC = %0.2f)' % (rocauc),
                 lw=2, alpha=.8)
         
        plt.xlim([-0.05, 1.05])
        plt.ylim([-0.05, 1.05])
        plt.xlabel("False Positive Rate (FPR)")
        plt.ylabel("True Positive Rate (TPR)")
        plt.title('ROC Curve')
        plt.margins(.02)
        plt.legend()
        plt.grid()
        plt.show()
    
    def model_eval(self, train_y, train_X, test_y, test_x, cl1, cl2, cl3):
        
        model1 = self.selectedLearner(cl1).fit(self.train_X,self.train_y)
        model2 = self.selectedLearner(cl2).fit(self.train_X,self.train_y)
        model3 = self.selectedLearner(cl3).fit(self.train_X,self.train_y)
        
        plt.figure(figsize=(6, 6))
        
        fpr, tpr, thr = roc_curve(test_y, model1.predict_proba(test_x)[:,1])
        rocauc = roc_auc_score(test_y, model1.predict_proba(test_x)[:,1], average='micro')
        plt.plot(fpr, tpr, color='navy', label=str(cl1)+' (AUC = %0.4f)' %rocauc)
        
        # SVM
        fpr, tpr, thr = roc_curve(test_y, model2.predict_proba(test_x)[:,1])
        rocauc = roc_auc_score(test_y, model2.predict_proba(test_x)[:,1], average='micro')
        plt.plot(fpr, tpr, color='red', label=str(cl2)+' (AUC = %0.4f)' %rocauc)
        
        # Random forest
        fpr, tpr, thr = roc_curve(test_y, model3.predict_proba(test_x)[:,1])
        rocauc = roc_auc_score(test_y, model3.predict_proba(test_x)[:,1], average='micro')
        plt.plot(fpr, tpr, color='green', label=str(cl3)+' (AUC = %0.4f)' %rocauc)
        
        # figure properties
        plt.xlabel("False Positive Rate (FPR)")
        plt.ylabel("True Positive Rate (TPR)")
        plt.title('ROC Curve')
        plt.margins(.02)
        plt.legend()
        plt.grid(alpha=.3)
        plt.show()
        

class NBL2():
    
    def __init__(self):
        print("initializing 2 layered Naive Bayes")
        self.train_X = None
        self.train_y = None
        self.test_X = None
        self.test_y = None
        self.clf = None
    
    def fit_predict(self, clf, train_X, train_y, test_X, test_y, class_label):
        self.clf = clf
        self.train_X = train_X
        self.train_y = train_y
        self.test_X = test_X
        self.test_y = test_y
        self.class_label = class_label
        self.clf.fit(self.train_X, self.train_y)
        predicted_1 = pd.DataFrame(self.clf.predict(self.train_X), columns=['predicted'])
        df = pd.concat([self.train_X, self.train_y], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df,predicted_1], axis=1)
        df = df[df['predicted'] == 1]
        df.drop(['predicted'], axis=1, inplace=True)
        train_y1 = df[self.class_label]
        df.drop([self.class_label], axis=1, inplace=True)
        train_X1 = df
        
        # Layer 2
        clf1 = GaussianNB()
        clf1.fit(train_X1, train_y1)
 
        predicted_2 = pd.DataFrame(self.clf.predict(self.test_X), columns=['predicted'])
        df = pd.concat([self.test_X, self.test_y], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df, predicted_2], axis=1)
        df_1 = df[df['predicted'] == 0]
        test_y1 = df_1[self.class_label]
        test_y1 = pd.DataFrame(test_y1, columns=[self.class_label])
        ftest_y1 = df_1['predicted']
        ftest_y1 = pd.DataFrame(ftest_y1, columns=['predicted'])
        df_2 = df[df['predicted'] == 1]
        predict_1 = df_1['predicted']
        predict_1 = pd.DataFrame(predict_1, columns=['predicted'])
        df_2.drop(['predicted'], axis=1, inplace=True)
        test_y2 = df_2[self.class_label]
        test_y2 = pd.DataFrame(test_y2, columns=[self.class_label])
        df_2.drop([self.class_label], axis=1, inplace=True)
        test_X2 = df_2
        predict_2 = clf1.predict(test_X2)       
        predict_2 = pd.DataFrame(predict_2, columns=['predicted'])
        predict = ftest_y1.append(predict_2)
        self.test_y = test_y1.append(test_y2)
        print(metrics.classification_report(self.test_y, predict, digits=3))
        print(metrics.confusion_matrix(self.test_y, predict))
        res =  [metrics.f1_score(self.test_y, predict,average='weighted'),
                metrics.accuracy_score(self.test_y, predict),metrics.roc_auc_score(self.test_y, predict, average='weighted')]
        return res, predict, self.test_y


class NBL3():
    
    def __init__(self):
        print("initializing 3 layered Naive Bayes")
        self.train_X = None
        self.train_y = None
        self.test_X = None
        self.test_y = None
        self.clf = None
    
    def fit_predict(self, clf, train_X, train_y, test_X, test_y, class_label):
        self.clf = clf
        self.train_X = train_X
        self.train_y = train_y
        self.test_X = test_X
        self.test_y = test_y
        self.class_label = class_label

        # Training
        # Layer 1
        self.clf.fit(self.train_X,self.train_y)
        
        # Layer 2
        predicted_1 = pd.DataFrame(self.clf.predict(self.train_X), columns=['predicted'])
        df = pd.concat([self.train_X, self.train_y], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df,predicted_1], axis=1)
        df_0 = df[df['predicted'] == 0]
        df = df[df['predicted'] == 1]
        
        df.drop(['predicted'], axis = 1, inplace = True)
        train_y1 = df[self.class_label]
        df.drop([self.class_label], axis = 1, inplace = True)
        train_X1 = df
        clf1 = GaussianNB()
        clf1.fit(train_X1,train_y1)
        
        df_0.drop(['predicted'], axis=1, inplace=True)
        train_y0 = df_0[self.class_label]
        df_0.drop([self.class_label], axis=1, inplace=True)
        train_X0 = df_0
        clf0 = GaussianNB()
        clf0.fit(train_X0, train_y0)
        
        # Layer 2
        predicted_2 = pd.DataFrame(clf1.predict(train_X1), columns=['predicted'])
        df = pd.concat([train_X1, train_y1], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df,predicted_2], axis=1)
        df_0 = df[df['predicted'] == 0]
        df = df[df['predicted'] == 1]
        
        df.drop(['predicted'], axis=1, inplace=True)
        train_y2 = df[self.class_label]
        df.drop([self.class_label], axis=1, inplace=True)
        train_X2 = df
        clf11 = GaussianNB()
        clf11.fit(train_X2,train_y2)

        df_0.drop(['predicted'], axis=1, inplace=True)
        train_y02 = df_0[self.class_label]
        df_0.drop([self.class_label], axis=1, inplace=True)
        train_X02 = df_0
        clf10 = GaussianNB()
        clf10.fit(train_X02, train_y02)

        predicted_02 = pd.DataFrame(clf0.predict(train_X0), columns=['predicted'])
        df = pd.concat([train_X0, train_y0], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df,predicted_02], axis=1)
        df_0 = df[df['predicted'] == 0]
        df = df[df['predicted'] == 1]
        
        df.drop(['predicted'], axis=1, inplace=True)
        train_y20 = df[self.class_label]
        df.drop([self.class_label], axis=1, inplace=True)
        train_X20 = df
        clf01 = GaussianNB()
        clf01.fit(train_X20, train_y20)
             
        df_0.drop(['predicted'], axis=1, inplace=True)
        train_y020 = df_0[self.class_label]
        df_0.drop([self.class_label], axis=1, inplace=True)
        train_X020 = df_0
        clf00 = GaussianNB()
        clf00.fit(train_X020, train_y020)
        
        # New layer
        predicted_21 = pd.DataFrame(clf11.predict(train_X2), columns=['predicted'])
        df1 = pd.concat([train_X2,train_y2], axis=1)
        column_names = df1.columns.values.tolist()
        df = np.array(df1)
        df = pd.DataFrame(df, columns=column_names)
        df = pd.concat([df,predicted_21], axis=1)
        df_0 = df[df['predicted'] == 0]
        df = df[df['predicted'] == 1]
        
        df.drop(['predicted'], axis=1, inplace=True)
        train_y111 = df[self.class_label]
        df.drop([self.class_label], axis=1, inplace=True)
        train_X111 = df
        clf111 = GaussianNB()
        clf111.fit(train_X111, train_y111)
        
        df_0.drop(['predicted'], axis=1, inplace=True)
        train_y110 = df_0[self.class_label]
        df_0.drop([self.class_label], axis=1, inplace=True)
        train_X110 = df_0
        clf110 = GaussianNB()
        clf110.fit(train_X110,train_y110)

        # Layer 1
        fpredicted = pd.DataFrame(self.clf.predict(self.test_X), columns=['predicted'])
        df = pd.concat([self.test_X, self.test_y], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df, fpredicted], axis=1)
        
        # class 0
        df_1 = df[df['predicted'] == 0] 
        predict_0 = df_1['predicted']
        predict_0 = pd.DataFrame(predict_0, columns=['predicted'])
        df_1.drop(['predicted'], axis=1, inplace=True)
        test_y0 = df_1[self.class_label]
        test_y0 = pd.DataFrame(test_y0, columns=[self.class_label])    # original label for model 0
        df_1.drop([self.class_label], axis=1, inplace=True)
        test_X0 = df_1

        # class 1
        df_2 = df[df['predicted'] == 1]
        predict_1 = df_2['predicted']
        predict_1 = pd.DataFrame(predict_1, columns=['predicted'])
        df_2.drop(['predicted'], axis=1, inplace=True)
        test_y1 = df_2[self.class_label]
        test_y1 = pd.DataFrame(test_y1, columns=[self.class_label])
        df_2.drop([self.class_label], axis=1, inplace=True)
        test_X1 = df_2

        # Layer 2
        # label 0
        fpredicted_0 = pd.DataFrame(clf0.predict(test_X0), columns=['predicted'])
        df = pd.concat([test_X0, test_y0], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df, fpredicted_0], axis=1)
        
        # class 0
        df_1 = df[df['predicted'] == 0]
        predict_00 = df_1['predicted']
        predict_00 = pd.DataFrame(predict_00, columns=['predicted'])
        df_1.drop(['predicted'], axis=1, inplace=True)
        test_y00 = df_1[self.class_label]
        test_y00 = pd.DataFrame(test_y00, columns=[self.class_label])   # original label for model 02
        df_1.drop([self.class_label], axis=1, inplace=True)
        test_X00 = df_1

        # class 1
        df_2 = df[df['predicted'] == 1]
        predict_01 = df_2['predicted']
        predict_01 = pd.DataFrame(predict_01, columns=['predicted'])
        df_2.drop(['predicted'], axis=1, inplace=True)
        test_y01 = df_2[self.class_label]
        test_y01 = pd.DataFrame(test_y01, columns=[self.class_label])
        df_2.drop([self.class_label], axis=1, inplace=True)
        test_X01 = df_2
        
        # Label 1
        fpredicted_1 = pd.DataFrame(clf1.predict(test_X1), columns=['predicted'])
        df = pd.concat([test_X1, test_y1], axis=1)
        df.reset_index(inplace=True)
        df = pd.concat([df, fpredicted_1], axis=1)
        
        # class 0
        df_1 = df[df['predicted'] == 0]
        predict_10 = df_1['predicted']
        predict_10 = pd.DataFrame(predict_10, columns=['predicted'])
        df_1.drop(['predicted'], axis=1, inplace=True)
        test_y10 = df_1[self.class_label]
        test_y10 = pd.DataFrame(test_y10, columns=[self.class_label])   # original label for model 02
        df_1.drop([self.class_label], axis=1, inplace=True)
        test_X10 = df_1

        # class 1
        df_2 = df[df['predicted'] == 1]
        predict_11 = df_2['predicted']
        predict_11 = pd.DataFrame(predict_11, columns=['predicted'])
        df_2.drop(['predicted'], axis=1, inplace=True)
        test_y11 = df_2[self.class_label]
        test_y11 = pd.DataFrame(test_y11, columns=[self.class_label])
        df_2.drop([self.class_label], axis=1, inplace=True)
        test_X11 = df_2

        # new layer
        fpredicted_11 = pd.DataFrame(clf11.predict(test_X11), columns=['predicted'])
        df1 = pd.concat([test_X11,test_y11], axis=1)
        column_names = df1.columns.values.tolist()
        df = np.array(df1)
        df = pd.DataFrame(df, columns=column_names)
        df = pd.concat([df, fpredicted_11], axis=1)
        
        df_1 = df[df['predicted'] == 0]
        predict_110 = df_1['predicted']
        predict_110 = pd.DataFrame(predict_110, columns=['predicted'])
        df_1.drop(['predicted'], axis=1, inplace=True)
        test_y110 = df_1[self.class_label]
        test_y110 = pd.DataFrame(test_y110, columns=[self.class_label])   # original label for model 02
        df_1.drop([self.class_label], axis=1, inplace=True)
        test_X110 = df_1

        # class 1
        df_2 = df[df['predicted'] == 1]
        predict_111 = df_2['predicted']
        predict_111 = pd.DataFrame(predict_111, columns=['predicted'])
        df_2.drop(['predicted'], axis=1, inplace=True)
        test_y111 = df_2[self.class_label]
        test_y111 = pd.DataFrame(test_y111, columns=[self.class_label])
        df_2.drop([self.class_label], axis=1, inplace=True)
        test_X111 = df_2

        # Layer 3
        predicted_00 = clf00.predict(test_X00)
        predicted_00 = pd.DataFrame(predicted_00, columns=['predicted'])
        predicted_01 = clf01.predict(test_X01)
        predicted_01 = pd.DataFrame(predicted_01, columns=['predicted'])
        predicted_10 = clf10.predict(test_X10)
        predicted_10 = pd.DataFrame(predicted_10, columns=['predicted'])
        predicted_110 = clf01.predict(test_X110)
        predicted_110 = pd.DataFrame(predicted_110, columns=['predicted'])
        predicted_111 = clf01.predict(test_X111)
        predicted_111 = pd.DataFrame(predicted_111, columns=['predicted'])
        
        predict = predicted_00.append(predicted_01)
        predict = predict.append(predicted_10)
        predict = predict.append(predicted_110)
        predict = predict.append(predicted_111)
        
        self.test_y = test_y00.append(test_y01)
        self.test_y = self.test_y.append(test_y10)
        self.test_y = self.test_y.append(test_y110)
        self.test_y = self.test_y.append(test_y111)
  
        print(metrics.classification_report(self.test_y, predict, digits=3))
        print(metrics.confusion_matrix(self.test_y, predict))

        res =  [metrics.f1_score(self.test_y, predict,average='weighted'),
                metrics.accuracy_score(self.test_y, predict),metrics.roc_auc_score(self.test_y, predict, average='weighted')]
        return res, predict, self.test_y
