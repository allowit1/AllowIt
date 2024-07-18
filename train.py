import pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split



def main():
    gnb = GaussianNB()
    df = pd.read_csv('data.csv')
    X, y = df.drop('Label', axis=1), df['Label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.8, random_state=0)
    gnb.fit(X_train, y_train)
    y_pred = gnb.predict(X_test)
    print("Number of mislabeled points out of a total %d points : %d" % (X_test.shape[0], (y_test != y_pred).sum()))

main()