from sklearn.model_selection import train_test_split
import pickle
from collections import Counter
import tensorflow.contrib.keras as kr
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
import random
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_recall_fscore_support
import warnings
warnings.filterwarnings('ignore')

class TextConfig():
    vocab_size = 5000
    seq_length = 600
    embedding_dim = 64  # 词向量维度
    num_classes = 4  # 类别数
    num_filters = 256  # 卷积核数目
    kernel_size = 5  # 卷积核尺
    hidden_dim = 128  # 全连接层神经元
    dropout_keep_prob = 0.5  # dropout保留比例
    learning_rate = 1e-3  # 学习率
    batch_size = 32  # 每批训练大小
    print_per_batch = 10
    num_iteration = 100

class TextClassification():
    def config(self):
        textConfig = TextConfig()
        self.vocab_size = textConfig.vocab_size
        self.seq_length = textConfig.seq_length
        self.embedding_dim = textConfig.embedding_dim
        self.num_classes = textConfig.num_classes
        self.num_filters = textConfig.num_filters
        self.kernel_size = textConfig.kernel_size
        self.hidden_dim = textConfig.hidden_dim
        self.dropout_keep_prob = textConfig.dropout_keep_prob
        self.learning_rate = textConfig.learning_rate
        self.batch_size = textConfig.batch_size
        self.print_per_batch = textConfig.print_per_batch
        self.num_iteration = textConfig.num_iteration

    def __init__(self, *args):
        self.config()
        if len(args) == 2:
            content_list = args[0]
            label_list = args[1]
            train_X, test_X, train_y, test_y = train_test_split(content_list, label_list)
            self.train_content_list = train_X
            self.train_label_list = train_y
            self.test_content_list = test_X
            self.test_label_list = test_y
            self.content_list = self.train_content_list + self.test_content_list
        elif len(args) == 4:
            self.train_content_list = args[0]
            self.train_label_list = args[1]
            self.test_content_list = args[2]
            self.test_label_list = args[3]
            self.content_list = self.train_content_list + self.test_content_list
        else:
            print('false to init TextClassification object')

    def getVocabularyList(self, content_list, vocabulary_size):
        allContent_str = ''.join(content_list)
        counter = Counter(allContent_str)
        vocabulary_list = [k[0] for k in counter.most_common(vocabulary_size)]
        return ['PAD'] + vocabulary_list

    def prepareData(self):
        vocabulary_list = self.getVocabularyList(self.content_list, self.vocab_size)
        if len(vocabulary_list) < self.vocab_size:
            self.vocab_size = len(vocabulary_list)
        contentLength_list = [len(k) for k in self.train_content_list]
        if max(contentLength_list) < self.seq_length:
            self.seq_length = max(contentLength_list)
        self.word2id_dict = dict([(b, a) for a, b in enumerate(vocabulary_list)])
        self.labelEncoder = LabelEncoder()
        self.labelEncoder.fit(train_label_list)

    def content2idList(self, content):
        return [self.word2id_dict[word] for word in content if word in self.word2id_dict]

    def content2X(self, content_list):
        idlist_list = [self.content2idList(content) for content in content_list]
        X = kr.preprocessing.sequence.pad_sequences(idlist_list, self.seq_length)
        return X

    def label2Y(self, label_list):
        y = self.labelEncoder.transform(label_list)
        Y = kr.utils.to_categorical(y, self.num_classes)
        return Y

    def buildModel(self):
        tf.reset_default_graph()
        self.X_holder = tf.placeholder(tf.int32, [None, self.seq_length])
        self.Y_holder = tf.placeholder(tf.float32, [None, self.num_classes])
        embedding = tf.get_variable('embedding', [self.vocab_size, self.embedding_dim])
        embedding_inputs = tf.nn.embedding_lookup(embedding, self.X_holder)
        conv = tf.layers.conv1d(embedding_inputs, self.num_filters, self.kernel_size)
        max_pooling = tf.reduce_max(conv, reduction_indices=[1])
        full_connect = tf.layers.dense(max_pooling, self.hidden_dim)
        full_connect_dropout = tf.contrib.layers.dropout(full_connect, keep_prob=self.dropout_keep_prob)
        full_connect_activate = tf.nn.relu(full_connect_dropout)
        softmax_before = tf.layers.dense(full_connect_activate, self.num_classes)
        self.predict_Y = tf.nn.softmax(softmax_before)
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits_v2(labels=self.Y_holder, logits=softmax_before)
        self.loss = tf.reduce_mean(cross_entropy)
        optimizer = tf.train.AdamOptimizer(self.learning_rate)
        self.train = optimizer.minimize(self.loss)
        self.predict_y = tf.argmax(self.predict_Y, 1)
        isCorrect = tf.equal(tf.argmax(self.Y_holder, 1), self.predict_y)
        self.accuracy = tf.reduce_mean(tf.cast(isCorrect, tf.float32))

    def trainModel(self):
        self.prepareData()
        self.buildModel()
        init = tf.global_variables_initializer()
        self.session = tf.Session()
        self.session.run(init)
        train_X = self.content2X(self.train_content_list)
        train_Y = self.label2Y(self.train_label_list)
        test_X = self.content2X(self.test_content_list)
        test_Y = self.label2Y(self.test_label_list)
        for i in range(self.num_iteration):
            selected_index = random.sample(list(range(len(train_Y))), k=self.batch_size)
            batch_X = train_X[selected_index]
            batch_Y = train_Y[selected_index]
            self.session.run(self.train, {self.X_holder: batch_X, self.Y_holder: batch_Y})
            step = i + 1
            if step % self.print_per_batch == 0 or step == 1:
                selected_index = random.sample(list(range(len(test_Y))), k=200)
                batch_X = test_X[selected_index]
                batch_Y = test_Y[selected_index]
                loss_value, accuracy_value = self.session.run([self.loss, self.accuracy],\
                    {self.X_holder: batch_X, self.Y_holder: batch_Y})
                print('step:%d loss:%.4f accuracy:%.4f' %
                      (step, loss_value, accuracy_value))

    def predict(self, content_list):
        if type(content_list) == str:
            content_list = [content_list]
        batch_X = self.content2X(content_list)
        predict_y = self.session.run(self.predict_y, {self.X_holder:batch_X})
        predict_label_list = self.labelEncoder.inverse_transform(predict_y)
        return predict_label_list

    def predictAll(self):
        predict_label_list = []
        batch_size = 100
        for i in range(0, len(self.test_content_list), batch_size):
            content_list = test_content_list[i: i + batch_size]
            predict_label = self.predict(content_list)
            predict_label_list.extend(predict_label)
        return predict_label_list

    def printConfusionMatrix(self):
        predict_label_list = self.predictAll()
        df = pd.DataFrame(confusion_matrix(self.test_label_list, predict_label_list),
                     columns=self.labelEncoder.classes_,
                     index=self.labelEncoder.classes_)
        print(df)

    def printReportTable(self):
        predict_label_list = self.predictAll()
        reportTable = eval_model(self.test_label_list,
                                      predict_label_list,
                                      self.labelEncoder.classes_)
        print(reportTable)

def eval_model(y_true, y_pred, labels):
    # 计算每个分类的Precision, Recall, f1, support
    p, r, f1, s = precision_recall_fscore_support(y_true, y_pred)
    # 计算总体的平均Precision, Recall, f1, support
    tot_p = np.average(p, weights=s)
    tot_r = np.average(r, weights=s)
    tot_f1 = np.average(f1, weights=s)
    tot_s = np.sum(s)
    res1 = pd.DataFrame({
        u'Label': labels,
        u'Precision': p,
        u'Recall': r,
        u'F1': f1,
        u'Support': s
    })
    res2 = pd.DataFrame({
        u'Label': ['总体'],
        u'Precision': [tot_p],
        u'Recall': [tot_r],
        u'F1': [tot_f1],
        u'Support': [tot_s]
    })
    res2.index = [999]
    res = pd.concat([res1, res2])
    return res[['Label', 'Precision', 'Recall', 'F1', 'Support']]

if __name__ == '__main__':
    with open('train_content_list.pickle', 'rb') as file:
        train_content_list = pickle.load(file)
    with open('train_label_list.pickle', 'rb') as file:
        train_label_list = pickle.load(file)
    with open('test_content_list.pickle', 'rb') as file:
        test_content_list = pickle.load(file)
    with open('test_label_list.pickle', 'rb') as file:
        test_label_list = pickle.load(file)
    # model = TextClassification(train_content_list, train_label_list)
    # attribute_list = [model.train_content_list, model.train_label_list,
    #       model.test_content_list, model.test_label_list]
    # len_list = [len(k) for k in attribute_list]
    # print(len_list)
    # model = TextClassification(train_content_list, train_label_list,
    #                            test_content_list, test_label_list)
    # attribute_list = [model.train_content_list, model.train_label_list,
    #                   model.test_content_list, model.test_label_list]
    # len_list = [len(k) for k in attribute_list]
    # print(len_list)
    model = TextClassification(train_content_list, train_label_list,
                               test_content_list, test_label_list)
    model.trainModel()
    model.printConfusionMatrix()
    model.printReportTable()