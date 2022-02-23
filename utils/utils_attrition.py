# Here are some functions which helped us to make plots or prettify dataframes in $attrition$ notebook
from sklearn.tree._tree import TREE_LEAF
import pandas as pd
from IPython.core.display import HTML
from IPython.display import display_html
import warnings
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import confusion_matrix, recall_score, precision_score, accuracy_score
import matplotlib.pyplot as plt
from sklearn import tree

warnings.filterwarnings('ignore')


def import_data(wave):
    """brings 2 dataframes with all the features and series with y (panelpat)"""
    # we predict particular wave attrition based on previous one, therefore we subtract 1 from wave number
    wave = str(int(wave) - 1)
    political = pd.read_csv(f'data/data_online_political_w{wave}.csv')
    personal = pd.read_csv(f'data/data_online_personal_w{wave}.csv')
    y = personal['panelpat']
    personal.drop(['id', 'panelpat', 'age_group -sd2x2'], axis=1, inplace=True)
    political.drop(['id', 'panelpat'], axis=1, inplace=True)
    return personal, political, y


def get_metrics(X, y_true, clf):
    """returns precision and recall for drop class as well as general accuracy"""
    y_pred = cross_val_predict(estimator=clf, X=X, y=y_true)
    recall = recall_score(y_true, y_pred, average=None)[0]
    precision = precision_score(y_true, y_pred, average=None)[0]
    accuracy = accuracy_score(y_true, y_pred)
    return recall, precision, accuracy


# df to store all the performance metrics we use (we use it to plot results then)
metrics_index = ['Recall', 'Precision', 'Accuracy']*2
performance = pd.DataFrame(index=metrics_index)


def store_data_for_table(performance, X_train, y_train, X_test, y_test, clf):
    """concatenate metrics of all the models we use and store them in df together"""
    recall_train, precision_train, accuracy_train = get_metrics(
        X_train, y_train, clf)
    recall_test, precision_test, accuracy_test = get_metrics(
        X_test, y_test, clf)
    all_metrics = [recall_train, precision_train,
                   accuracy_train, recall_test, precision_test, accuracy_test]
    all_metrics = pd.Series(all_metrics, index=metrics_index)
    performance_ = pd.concat([performance, all_metrics], axis=1)
    return performance_


# Logistic Regression
def get_engineered_feature_names(X_train):
    engineered_feature_names = ['voting_age_awareness_w1',
                                'KNOWLEDGE_PARLIAMENTARY_THRESHOLD_w1',
                                'know_politicians_ratio',
                                'whether_dropped_before',
                                'lr_placement_correct',
                                'timeOfResponding',
                                'weekendResponse',
                                'whether_dropped_before',
                                'inconsistency',
                                'bad_quality',
                                'weekend',
                                'know_politicians_ratio',
                                'same_agree_resp',
                                'political_interest',
                                'dont_know_percentage_mean',
                                'days_to_respond']

    return X_train.loc[:, X_train.columns.isin(engineered_feature_names)].columns


def fancy_output_for_lr(coeffs, X_train):
    feature_coef = pd.DataFrame(coeffs)
    feature_coef.columns = X_train.columns
    feature_coef.index = ['coef']
    feature_coef = feature_coef.T

    feature_coef = sort_by_absolute_val(feature_coef, 'coef')

    engin_features = get_engineered_feature_names(X_train)
    feature_coef_m = feature_coef[:10]
    feature_coef_b = feature_coef[feature_coef.index.isin(engin_features)]

    df_m = feature_coef_m.style.set_table_attributes("style='display:inline'").set_caption(
        'The most important features and its coefficients obtained by logistic regression')
    df_b = feature_coef_b.style.set_table_attributes(
        "style='display:inline'").set_caption('Engineered features coefficients')
    display(HTML("<left><h4>"+'Logistic regression'+"</h4></left>"))
    display_html(df_m._repr_html_()+df_b._repr_html_(), raw=True)

# Decision Trees


# cutting unnessesary leaves
# https://stackoverflow.com/questions/51397109/prune-unnecessary-leaves-in-sklearn-decisiontreeclassifier


def is_leaf(inner_tree, index):
    # Check whether node is leaf node
    return (inner_tree.children_left[index] == TREE_LEAF and
            inner_tree.children_right[index] == TREE_LEAF)


def prune_index(inner_tree, decisions, index=0):
    """ Start pruning from the bottom - if we start from the top, we might miss
    nodes that become leaves during pruning.
    Do not use this directly - use prune_duplicate_leaves instead."""
    if not is_leaf(inner_tree, inner_tree.children_left[index]):
        prune_index(inner_tree, decisions, inner_tree.children_left[index])
    if not is_leaf(inner_tree, inner_tree.children_right[index]):
        prune_index(inner_tree, decisions, inner_tree.children_right[index])

    # Prune children if both children are leaves now and make the same decision:
    if (is_leaf(inner_tree, inner_tree.children_left[index]) and
        is_leaf(inner_tree, inner_tree.children_right[index]) and
        (decisions[index] == decisions[inner_tree.children_left[index]]) and
            (decisions[index] == decisions[inner_tree.children_right[index]])):
        # turn node into a leaf by "unlinking" its children
        inner_tree.children_left[index] = TREE_LEAF
        inner_tree.children_right[index] = TREE_LEAF


def prune_duplicate_leaves(mdl):
    decisions = mdl.tree_.value.argmax(
        axis=2).flatten().tolist()  # Decision for each node
    prune_index(mdl.tree_, decisions)


def fancy_plotting_for_DT(clf, X_train, names):
    display(HTML("<left><h4>"+'Decision tree'+"</h4></left>"))
    print('Best classifier from GridSearch:')
    display(clf.best_estimator_)
    X_train.feature_names = X_train.columns
    plt.figure(figsize=(28, 10))
    _ = tree.plot_tree(clf.best_estimator_, filled=True,
                       feature_names=X_train.feature_names, proportion=True, rounded=True, fontsize=15, class_names=names)
    plt.show()

# general helpers


def scale_train(X_train, X_test):
    cols = X_train.columns
    scaler = MinMaxScaler()
    scaler.fit(X_train)
    X_train = scaler.transform(X_train)
    X_train = pd.DataFrame(X_train)
    X_train.columns = cols
    X_test = scaler.transform(X_test)
    X_test = pd.DataFrame(X_test)
    X_test.columns = cols
    return X_train, X_test


def sort_by_absolute_val(df, column):
    """Sort df column by descending order in terms of the absolute value."""
    df = df.reindex(df[column]
                    .abs()
                    .sort_values(ascending=False)
                    .index)
    return df


def horizontal_line():
    print(' ')
    line = "<hr/>"
    return display(HTML(line))


def h2centered(text):
    formatted_text = "<center><h3>"+text+"</h3></center>"
    return display(HTML(formatted_text))


def y_counter(y):
    """counts number of samples in each class, colors cells depending on label"""
    y_ = y.value_counts().to_frame()
    y_.index = ['stayed', 'dropped']
    color_cells = {"stayed": 'background-color: #e6ffe6',
                   "dropped": 'background-color: #ffe6e6'}
    y_ = y_.style.apply(lambda x: x.index.map(color_cells))
    return display(y_)
