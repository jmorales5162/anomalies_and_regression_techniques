import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn.ensemble import IsolationForest
import pandas as pd
import os
import Config2
from pathlib import Path
from sklearn.cluster import KMeans


# AutoEncoder
import tensorflow as tf
from tensorflow.keras import models, layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from autoencoder import AutoEncoder





def load_data(path):
    df1 = pd.read_csv(path, sep=',', decimal='.')
    selected_columns = ['W', 'radiation']
    df = df1[selected_columns] 
    df = normalize_data(df)
    return df


def normalize_data(df):
    new_min = 0
    new_max = 1

    # Normalize the DataFrame from -1 to 1 to 0 to 1
    normalized_df = (df + 1) / 2 * (new_max - new_min) + new_min
    return normalized_df


def d3plot():
    plt.rcParams["figure.figsize"] = [7.00, 3.50]
    plt.rcParams["figure.autolayout"] = True
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    data = np.random.random(size=(3, 3, 3))
    z, x, y = data.nonzero()
    ax.scatter(x, y, z, c=z, alpha=1)
    plt.show()


def isolationForest(data):
    resultados = np.zeros((3, data.shape[0])) # (3,52547)
    c = [0.01, 0.05, 0.1] 
    for i in range(len(c)):
        modelo = IsolationForest(contamination=c[i]).fit(data)
        resultados[i] = modelo.predict(data)
    
    # Graficar datos anomalos 
    plt.set_cmap("jet")
    fig = plt.figure(figsize=(13, 4))

    for i in range(len(c)):    
        ax = fig.add_subplot(1, 3, i+1)
        ax.scatter(data[resultados[i]==-1][:, 0], 
               data[resultados[i]==-1][:, 1], 
               c="skyblue", marker="s", s=50)
        ax.scatter(data[:, 0], 
               data[:, 1], 
               c=range(data.size//2), marker="x",
               s=50, alpha=0.6)
        ax.set_title("Contaminación: %0.2f" % c[i], size=18, color="purple")
        ax.set_ylabel("Radiacion", size=8)
        ax.set_xlabel("Watts", size=8)

    plt.show()




def kmeans(data):
    n_clusters = 3
    n_clusters_to_detect = n_clusters # Number of clusters (including anomalies)
    kmeans = KMeans(n_clusters=n_clusters_to_detect)
    kmeans.fit(data)
    # Predict cluster labels
    cluster_labels = kmeans.predict(data)

    # Find the cluster centers
    cluster_centers = kmeans.cluster_centers_
    # Calculate the distance from each point to its assigned cluster center
    distances = [np.linalg.norm(x - cluster_centers[cluster]) for x, cluster in zip(data, cluster_labels)]
    # Define a threshold for anomaly detection (e.g., based on the distance percentile)
    percentile_threshold = 99.5
    threshold_distance = np.percentile(distances, percentile_threshold)

    # Identify anomalies
    anomalies = [data[i] for i, distance in enumerate(distances) if distance > threshold_distance]
    anomalies = np.asarray(anomalies, dtype=np.float32)

    # Printing the clusters
    colors = cm.nipy_spectral(cluster_labels.astype(float) / 3)
    plt.scatter(data[:, 0], data[:, 1], marker='.', s=50, lw=0, alpha=0.7,c=colors, edgecolor='k')
    plt.scatter(anomalies[:, 0], anomalies[:, 1], color='red', marker='.', s=50, label='Anomalies')
    plt.show()



def autoEncoder(data):
    x_train, x_test, y_train, y_test = train_test_split(data.values, data.values[:,0:1], test_size=0.2, random_state=111)
    model = AutoEncoder()

    early_stopping = tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=2, mode="min")
    model.compile(optimizer='adam', loss="mae")
    history = model.fit(normal_train_data, normal_train_data, epochs=50, batch_size=120,
                    validation_data=(train_data_scaled[:,1:], train_data_scaled[:, 1:]),
                    shuffle=True,
                    callbacks=[early_stopping]
                    )
    encoder_out = model.encoder(normal_test_data).numpy() #8 unit representation of data
    decoder_out = model.decoder(encoder_out).numpy()
    plt.plot(normal_test_data[0], 'b')
    plt.plot(decoder_out[0], 'r')
    plt.title("Model performance on Normal data")
    plt.show()

    encoder_out_a = model.encoder(anomaly_test_data).numpy() #8 unit representation of data
    decoder_out_a = model.decoder(encoder_out_a).numpy()
    plt.plot(anomaly_test_data[0], 'b')
    plt.plot(decoder_out_a[0], 'r')
    plt.title("Model performance on Anomaly Data")
    plt.show()

    reconstruction = model.predict(normal_test_data)
    train_loss = tf.keras.losses.mae(reconstruction, normal_test_data)
    plt.hist(train_loss, bins=50)

    threshold = np.mean(train_loss) + 2*np.std(train_loss)
    reconstruction_a = model.predict(anomaly_test_data)
    train_loss_a = tf.keras.losses.mae(reconstruction_a, anomaly_test_data)
    plt.hist(train_loss_a, bins=50)
    plt.title("loss on anomaly test data")
    plt.show()

    plt.hist(train_loss, bins=50, label='normal')
    plt.hist(train_loss_a, bins=50, label='anomaly')
    plt.axvline(threshold, color='r', linewidth=3, linestyle='dashed', label='{:0.3f}'.format(threshold))
    plt.legend(loc='upper right')
    plt.title("Normal and Anomaly Loss")
    plt.show()


def autoEncoder2(data):
    x_train, x_test, y_train, y_test = train_test_split(data, data[:,0:1], test_size=0.2, random_state=111)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(x_train)
    X_test_scaled = scaler.fit_transform(x_test)
    autoencoder = models.Sequential()
    autoencoder.add(layers.Dense(1, input_shape=X_train_scaled.shape[1:], activation='relu'))
    autoencoder.add(layers.Dense(2))
    autoencoder.compile(optimizer='adam', loss='mse')
    autoencoder.summary()
    history = autoencoder.fit(X_train_scaled, X_train_scaled, 
          epochs=30, 
          batch_size=100,
          validation_data=(X_test_scaled, X_test_scaled),
          shuffle=True)
    
    mse_train = tf.keras.losses.mse(autoencoder.predict(X_train_scaled), X_train_scaled)
    umbral = np.max(mse_train)

    plt.figure(figsize=(12,4))
    plt.hist(mse_train, bins=50)
    plt.xlabel("Error de reconstrucción (entrenamiento)")
    plt.ylabel("Número de datos")
    plt.axvline(umbral, color='r', linestyle='--')
    plt.legend(["Umbral"], loc="upper center")
    plt.show()
    e_test = autoencoder.predict(X_test_scaled)

    mse_test = np.mean(np.power(X_test_scaled - e_test, 2), axis=1)
    plt.figure(figsize=(12,4))
    plt.plot(range(1,X_train_scaled.shape[0]+1),mse_train,'b.')
    plt.plot(range(X_train_scaled.shape[0]+1,X_train_scaled.shape[0]+X_test_scaled.shape[0]+1),mse_test,'r.')
    plt.axhline(umbral, color='r', linestyle='--')
    plt.xlabel('Índice del dato')
    plt.ylabel('Error de reconstrucción');
    plt.legend(["Entrenamiento", "Test", "Umbral"], loc="upper left")
    plt.show()

if __name__ == "__main__":

    x1 = load_data(Config2.path)


    #isolationForest(x1.to_numpy())
    #kmeans(x1.to_numpy())
    autoEncoder2(x1.to_numpy())
    
    #df = pd.read_csv('spx.csv', parse_dates=['date'], index_col='date')
    #df.head()
  

    #x1 = x1.add_prefix('c')
    #print(x1)
    #print(x1)
    #print(x1.query('W > 0.299249'))
    #print(x1.query('W == 0.199249').values[:,1:])
    #x1['c0'].value_counts()
    #autoEncoder(x1)


