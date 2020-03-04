# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 10:11:00 2020

@author: Carlos Rodero García

Process file "Lroot_calculated_irradiances" obtained in
calculate-irradiances-Hydrolight script to obtain kfunctions (Kd, Ku or Kl).

"""
import os
import pandas as pd
from scipy import stats
import io
import math
import sys
import time
import threading
import warnings


class ProcessIrradFile:
    """
    Open Lroot_calculated_irradiances.csv
    Create dataframe from content of file
    Obtain kfunctions from irradiances Ed, Eu and El
    """

    def __init__(self):

        # class variables
        self.file_name = "Lroot_calculated_irradiances.csv"
        self.path_files_raw = "files/raw"
        self.path_files_csv = "files/csv"
        self.content = None
        self.df = pd.DataFrame()
        pd.options.mode.chained_assignment = None
        warnings.filterwarnings("ignore")

    def open_file(self):
        """
        Open file and get content of file
        """
        f = os.path.join(self.path_files_raw, self.file_name)
        try:
            with open(f, 'r') as file:
                self.content = file.read()

        except FileNotFoundError:
            print(f"File {self.file_name} not found")
            exit()

    def _create_dataframe_from_Lroot_calc_irrad(self):
        """
        Create dataframe from content file
        """
        # Create dataframe from content of .csv file
        self.df = pd.read_csv(io.StringIO(self.content), header=0,
                              skipinitialspace=True, index_col=0)

    def create_dataframe_from_Lroot_calc_irrad(self):
        """
        Create new thread to process create dataframe
        """
        the_process = threading.Thread(
            target=self._create_dataframe_from_Lroot_calc_irrad)
        the_process.start()
        while the_process.is_alive():
            self.animated_loading(process_name="Create Dataframe")

    def _calculate_kfunctions(self):
        """
        Calculate kfunctions Kd, Ku and Kl

        Return
        ------
            df_final: pandas dataframe object
                dataframe with Kd values
        """
        # add columns to dataframe
        # Calculate K-functions as a negative of the slope of liner regression
        # with last 2 elements z2 and z1
        self.df['calculated_Kd_LR'] = 0
        self.df['calculated_Ku_LR'] = 0
        self.df['calculated_Kl1_LR'] = 0
        self.df['calculated_Kl2_LR'] = 0

        self.df['r2value_Kd_LR'] = 0
        self.df['r2value_Ku_LR'] = 0
        self.df['r2value_Kl1_LR'] = 0
        self.df['r2value_Kl2_LR'] = 0

        # Calculate K-functions as a negative of the slope of liner regression
        # with all elements, except points in depths at -1.0 and 0.0
        self.df['calculated_Kd_LR_all_points'] = 0
        self.df['calculated_Ku_LR_all_points'] = 0
        self.df['calculated_Kl1_LR_all_points'] = 0
        self.df['calculated_Kl2_LR_all_points'] = 0

        self.df['r2value_Kd_LR_all_points'] = 0
        self.df['r2value_Ku_LR_all_points'] = 0
        self.df['r2value_Kl1_LR_all_points'] = 0
        self.df['r2value_Kl2_LR_all_points'] = 0

        # Calculate K-functions as it is calculated in HydroLight
        self.df['calculated_Kd_HL'] = 0
        self.df['calculated_Ku_HL'] = 0
        self.df['calculated_Kl1_HL'] = 0
        self.df['calculated_Kl2_HL'] = 0

        # assign float to lambda and depth in dataframe
        self.df['lambda'] = self.df['lambda'].astype(float).fillna(0.0)
        self.df['depth'] = self.df['depth'].astype(float).fillna(0.0)

        self.df = self.df.apply(pd.to_numeric, args=('coerce',))

        # init variables
        lmbd = self.df['lambda'].iloc[0]

        x = []

        log_y_kd = []
        log_y_ku = []
        log_y_kl1 = []
        log_y_kl2 = []

        y_kd = []
        y_ku = []
        y_kl1 = []
        y_kl2 = []

        # Calculate df linear regression
        print(f" - Start in lambda = {lmbd}")

        for i in range(0, len(self.df)):

            depth = self.df['depth'].iloc[i]

            # clear variables in each new lambda
            if lmbd != self.df['lambda'].iloc[i]:
                lmbd = self.df['lambda'].iloc[i]
                x = []

                log_y_kd = []
                log_y_ku = []
                log_y_kl1 = []
                log_y_kl2 = []

                y_kd = []
                y_ku = []
                y_kl1 = []
                y_kl2 = []
                print(f" - Calculate in lambda = {lmbd}")

            # Calculate k-functions. When we calculate all points of linear
            # regression we do not calculate in depths of -1.0 and 0.0
            if not math.isnan(depth):
                x.append(self.df['depth'].iloc[i])

                log_y_kd.append(math.log(self.df['calculated_Ed'].iloc[i]))
                log_y_ku.append(math.log(self.df['calculated_Eu'].iloc[i]))
                log_y_kl1.append(math.log(self.df['calculated_El1'].iloc[i]))
                log_y_kl2.append(math.log(self.df['calculated_El2'].iloc[i]))

                y_kd.append(self.df['calculated_Ed'].iloc[i])
                y_ku.append(self.df['calculated_Eu'].iloc[i])
                y_kl1.append(self.df['calculated_El1'].iloc[i])
                y_kl2.append(self.df['calculated_El2'].iloc[i])

            # Calculate Kd
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_kd[-2:])
                self.df['calculated_Kd_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Kd_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_kd[2:])
                if math.isnan(slope):
                    self.df['calculated_Kd_LR_all_points'].iloc[i] = 0
                else:
                    self.df['calculated_Kd_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Kd_LR_all_points'].iloc[i] = r_value * r_value

                self.df['calculated_Kd_HL'].iloc[i] = (
                    math.log(y_kd[-1] / y_kd[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Kd_LR'].iloc[i] = 0
                self.df['r2value_Kd_LR'].iloc[i] = 0
                self.df['calculated_Kd_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kd_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kd_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Kd_LR'].iloc[i] = 0
                self.df['r2value_Kd_LR'].iloc[i] = 0
                self.df['calculated_Kd_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kd_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kd_HL'].iloc[i] = 0

            # Calculate Ku
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_ku[-2:])
                self.df['calculated_Ku_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Ku_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_ku[2:])
                if math.isnan(slope):
                    self.df['calculated_Ku_LR_all_points'].iloc[i] = 0
                else:
                    self.df['calculated_Ku_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Ku_LR_all_points'].iloc[i] = r_value*r_value

                self.df['calculated_Ku_HL'].iloc[i] = (
                    math.log(y_ku[-1] / y_ku[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Ku_LR'].iloc[i] = 0
                self.df['r2value_Ku_LR'].iloc[i] = 0
                self.df['calculated_Ku_LR_all_points'].iloc[i] = 0
                self.df['r2value_Ku_LR_all_points'].iloc[i] = 0
                self.df['calculated_Ku_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Ku_LR'].iloc[i] = 0
                self.df['r2value_Ku_LR'].iloc[i] = 0
                self.df['calculated_Ku_LR_all_points'].iloc[i] = 0
                self.df['r2value_Ku_LR_all_points'].iloc[i] = 0
                self.df['calculated_Ku_HL'].iloc[i] = 0

            # Calculate Kl1
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_kl1[-2:])
                self.df['calculated_Kl1_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Kl1_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_kl1[2:])
                if math.isnan(slope):
                    self.df['calculated_Kl1_LR_all_points'].iloc[i] = 0
                else:
                    self.df[
                        'calculated_Kl1_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Kl1_LR_all_points'].iloc[i] = r_value*r_value

                self.df['calculated_Kl1_HL'].iloc[i] = (
                    math.log(y_kl1[-1] / y_kl1[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Kl1_LR'].iloc[i] = 0
                self.df['r2value_Kl1_LR'].iloc[i] = 0
                self.df['calculated_Kl1_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl1_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl1_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Kl1_LR'].iloc[i] = 0
                self.df['r2value_Kl1_LR'].iloc[i] = 0
                self.df['calculated_Kl1_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl1_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl1_HL'].iloc[i] = 0

            # Calculate Kl2
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_kl2[-2:])
                self.df['calculated_Kl2_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Kl2_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_kl2[2:])
                if math.isnan(slope):
                    self.df['calculated_Kl2_LR_all_points'].iloc[i] = 0
                else:
                    self.df[
                        'calculated_Kl2_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Kl2_LR_all_points'].iloc[i] = r_value*r_value

                self.df['calculated_Kl2_HL'].iloc[i] = (
                    math.log(y_kl2[-1] / y_kl2[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Kl2_LR'].iloc[i] = 0
                self.df['r2value_Kl2_LR'].iloc[i] = 0
                self.df['calculated_Kl2_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl2_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl2_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Kl2_LR'].iloc[i] = 0
                self.df['r2value_Kl2_LR'].iloc[i] = 0
                self.df['calculated_Kl2_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl2_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl2_HL'].iloc[i] = 0

        # save as csv
        fname = f"{self.file_name.split('.')[0]}_calculated_kfunctions.csv"
        f = os.path.join(self.path_files_csv, fname)
        self.df.to_csv(f)

    def calculate_kfunctions(self):
        the_process = threading.Thread(
            target=self._calculate_kfunctions)
        start = time.time()
        the_process.start()
        while the_process.is_alive():
            self.animated_loading(process_name="Calculate kfunctions")
        end = time.time()
        print("\nComplete. ")
        print(f"Time calculating kfunctions: {(end - start)/60} minutes")

    def animated_loading(self, process_name=""):
        chars = r"/—\|"
        for char in chars:
            sys.stdout.write('\r'+f'{process_name} - Loading...'+char)
            time.sleep(.1)
            sys.stdout.flush()


if __name__ == "__main__":

    prf = ProcessIrradFile()
    prf.open_file()
    prf.create_dataframe_from_Lroot_calc_irrad()
    prf.calculate_kfunctions()
