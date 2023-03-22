# % source: https://www.datacamp.com/tutorial/principal-component-analysis-in-python

from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from upAndDownload.stash_communication import StashInterface
from Parsing.parseFunctions import data_dict_to_dataframe, timestamp_from_datetime, \
    interpolate_frequency_from_pd_series, get_mean_noise
from auxiliaryParsing import pickleFunctions
import pandas as pd
import seaborn as sns
import networkx as nx
import scipy
from datetime import datetime as dt


def pca_plot(pca_total, z_data, parameter):
    # plot
    fig = plt.figure(figsize=(10, 8))
    plt.xlabel('Principal Component - 1', fontsize=20)
    plt.ylabel('Principal Component - 2', fontsize=20)
    plt.title("PCA Flight Analysis", fontsize=20)
    # for target, color in zip(targets, colors):
    # indicesToKeep = breast_dataset['label'] == correlation[target]
    ax1 = plt.scatter(pca_total.loc[:, 'principal component 1'],
                      pca_total.loc[:, 'principal component 2'], c=z_data, s=1)

    fig.colorbar(ax1, label=parameter)
    plt.show()


if __name__ == "__main__":

    # flight = pickleFunctions.loosen(r"C:\Users\klei_cl\Desktop\temp\D-CODE\2022-11-16_GBAS_GR-#3.pickle")
    """
    df = data_dict_to_dataframe(flight)
    df = df._get_numeric_data().dropna()
    """

    stash_io = StashInterface("dev")
    sensor_list = stash_io.download_series_list("6407225c6ff39c8dec1ea03a")
    # find abstract sensor class for each sensor

    df = stash_io.download_flight("639d04757f46b2ad8d943b0a", parameters=["FD_RUDDER"],
                                  sampling_rate=50)


    signals = [df["FD_RUDDER"]]
    fig, axs = plt.subplots(2, 1)
    for n, signal in enumerate(signals):
        mean_noise = get_mean_noise(signal)
        axs[0, n].plot(signal)
        axs[0, n].set_title(signal.name)
        axs[1, n].plot(mean_noise, "g")
        axs[1, 0].set_title("Logarithmic Amplitude meaned over all frequencies")
    fig.show()

    f, t, Sxx = scipy.signal.spectrogram(signal)
    plt.pcolormesh(t, f, Sxx, shading='gouraud')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.show()

    # pca starts here
    x = StandardScaler().fit_transform(df.values)  # normalize
    pca_flight = PCA(n_components=2)
    principalComponents_flight = pca_flight.fit_transform(x)
    principal_flight_Df = pd.DataFrame(data=principalComponents_flight
                                       , columns=['principal component 1', 'principal component 2'])
    principal_flight_z = df.loc[:, parameter].values

    # Calculate the correlation between individuals. We have to transpose first, because the corr function calculate the pairwise correlations between columns.
    corr = df.corr()
    # Transform it in a links data frame (3 columns only):
    links = corr.stack().reset_index()
    links.columns = ['var1', 'var2', 'value']
    # Keep only correlation over a threshold and remove self correlation (cor(A,A)=1)
    links_filtered = links.loc[(links['value'] > 0.7) & (links['var1'] != links['var2'])]
    # Build your graph
    G = nx.from_pandas_edgelist(links_filtered, 'var1', 'var2')
    # Plot the network:
    nx.draw(G, with_labels=True, node_color='orange', node_size=400, edge_color='black', linewidths=1, font_size=5)

    sns.heatmap(df.corr(), annot=False, xticklabels=True, yticklabels=True)
    plt.title("Parameter Correlation")
    plt.show()
    sns.heatmap(df.cov(), annot=False, xticklabels=True, yticklabels=True)
    plt.title("Parameter Linear Covariance")
    plt.show()

    # covariance eigenvalue bar graph
    eigenvalues = np.array([(feature ** 2).sum() for feature in pca_flight.components_.transpose()])
    columns_sorted = [line for (time, line) in sorted(zip(eigenvalues, df.columns.to_list()))]
    eigenvalues_sorted = sorted(eigenvalues)
    df_eigenvalues = pd.DataFrame(columns=columns_sorted, data=np.array(eigenvalues_sorted, ndmin=2))
    plt.bar(df_eigenvalues.columns, height=df_eigenvalues.values.tolist()[0])
    plt.xticks(rotation=90)

    pca_plot(principal_flight_Df, principal_flight_z, parameter)

    # TODO: get datadadict. Standardize values following z = (value-mean)/stdev

    # TODO: for all parameters that are floats

    # TODO: return datadict
