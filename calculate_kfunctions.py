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
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import plotly.graph_objs as go
from plotly.subplots import make_subplots


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

    def open_file(self, file_name=None, path_file=None):
        """
        Open file and get content of file

        Parameters
        ----------
            file_name: str
                Name of the file (Default=None)
            path_file: str
                Path of the file (Default=None)
        """
        if file_name is None:
            f = os.path.join(self.path_files_raw, self.file_name)
        else:
            f = os.path.join(path_file, file_name)
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
        self.df['calculated_Kl1_polar_cap_LR'] = 0
        self.df['calculated_Kl2_polar_cap_LR'] = 0
        self.df['calculated_Khc_LR'] = 0
        self.df['calculated_Khc_45_LR'] = 0

        self.df['r2value_Kd_LR'] = 0
        self.df['r2value_Ku_LR'] = 0
        self.df['r2value_Kl1_LR'] = 0
        self.df['r2value_Kl2_LR'] = 0
        self.df['r2value_Kl1_polar_cap_LR'] = 0
        self.df['r2value_Kl2_polar_cap_LR'] = 0
        self.df['r2value_Khc_LR'] = 0
        self.df['r2value_Khc_45_LR'] = 0

        # Calculate K-functions as a negative of the slope of liner regression
        # with all elements, except points in depths at -1.0 and 0.0
        self.df['calculated_Kd_LR_all_points'] = 0
        self.df['calculated_Ku_LR_all_points'] = 0
        self.df['calculated_Kl1_LR_all_points'] = 0
        self.df['calculated_Kl2_LR_all_points'] = 0
        self.df['calculated_Kl1_polar_cap_LR_all_points'] = 0
        self.df['calculated_Kl2_polar_cap_LR_all_points'] = 0
        self.df['calculated_Khc_LR_all_points'] = 0
        self.df['calculated_Khc_45_LR_all_points'] = 0

        self.df['r2value_Kd_LR_all_points'] = 0
        self.df['r2value_Ku_LR_all_points'] = 0
        self.df['r2value_Kl1_LR_all_points'] = 0
        self.df['r2value_Kl2_LR_all_points'] = 0
        self.df['r2value_Kl1_polar_cap_LR_all_points'] = 0
        self.df['r2value_Kl2_polar_cap_LR_all_points'] = 0
        self.df['r2value_Khc_LR_all_points'] = 0
        self.df['r2value_Khc_45_LR_all_points'] = 0

        # Calculate K-functions as it is calculated in HydroLight
        self.df['calculated_Kd_HL'] = 0
        self.df['calculated_Ku_HL'] = 0
        self.df['calculated_Kl1_HL'] = 0
        self.df['calculated_Kl2_HL'] = 0
        self.df['calculated_Kl1_polar_cap_HL'] = 0
        self.df['calculated_Kl2_polar_cap_HL'] = 0
        self.df['calculated_Khc_HL'] = 0
        self.df['calculated_Khc_45_HL'] = 0

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
        log_y_kl1_polar_cap = []
        log_y_kl2_polar_cap = []
        log_y_khc = []
        log_y_khc_45 = []

        y_kd = []
        y_ku = []
        y_kl1 = []
        y_kl2 = []
        y_kl1_polar_cap = []
        y_kl2_polar_cap = []
        y_khc = []
        y_khc_45 = []

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
                log_y_kl1_polar_cap = []
                log_y_kl2_polar_cap = []
                log_y_khc = []
                log_y_khc_45 = []

                y_kd = []
                y_ku = []
                y_kl1 = []
                y_kl2 = []
                y_kl1_polar_cap = []
                y_kl2_polar_cap = []
                y_khc = []
                y_khc_45 = []
                print(f" - Calculate in lambda = {lmbd}")

            # Calculate k-functions. When we calculate all points of linear
            # regression we do not calculate in depths of -1.0 and 0.0
            if not math.isnan(depth):
                x.append(self.df['depth'].iloc[i])

                log_y_kd.append(math.log(self.df['calculated_Ed'].iloc[i]))
                log_y_ku.append(math.log(self.df['calculated_Eu'].iloc[i]))
                log_y_kl1.append(math.log(self.df['calculated_El1_no_polar_cap'].iloc[i]))
                log_y_kl2.append(math.log(self.df['calculated_El2_no_polar_cap'].iloc[i]))
                log_y_kl1_polar_cap.append(math.log(self.df['calculated_El1_polar_cap'].iloc[i]))
                log_y_kl2_polar_cap.append(math.log(self.df['calculated_El2_polar_cap'].iloc[i]))
                log_y_khc.append(math.log(self.df['calculated_Ehc'].iloc[i]))
                log_y_khc_45.append(math.log(self.df['calculated_Ehc_45'].iloc[i]))

                y_kd.append(self.df['calculated_Ed'].iloc[i])
                y_ku.append(self.df['calculated_Eu'].iloc[i])
                y_kl1.append(self.df['calculated_El1_no_polar_cap'].iloc[i])
                y_kl2.append(self.df['calculated_El2_no_polar_cap'].iloc[i])
                y_kl1_polar_cap.append(self.df['calculated_El1_polar_cap'].iloc[i])
                y_kl2_polar_cap.append(self.df['calculated_El2_polar_cap'].iloc[i])
                y_khc.append(self.df['calculated_Ehc'].iloc[i])
                y_khc_45.append(self.df['calculated_Ehc_45'].iloc[i])

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

            # Calculate Kl1_polar_cap
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_kl1_polar_cap[-2:])
                self.df['calculated_Kl1_polar_cap_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Kl1_polar_cap_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_kl1_polar_cap[2:])
                if math.isnan(slope):
                    self.df['calculated_Kl1_polar_cap_LR_all_points'].iloc[i] = 0
                else:
                    self.df[
                        'calculated_Kl1_polar_cap_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Kl1_polar_cap_LR_all_points'].iloc[i] = r_value*r_value

                self.df['calculated_Kl1_polar_cap_HL'].iloc[i] = (
                    math.log(y_kl1_polar_cap[-1] / y_kl1_polar_cap[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Kl1_polar_cap_LR'].iloc[i] = 0
                self.df['r2value_Kl1_polar_cap_LR'].iloc[i] = 0
                self.df['calculated_Kl1_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl1_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl1_polar_cap_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Kl1_polar_cap_LR'].iloc[i] = 0
                self.df['r2value_Kl1_polar_cap_LR'].iloc[i] = 0
                self.df['calculated_Kl1_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl1_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl1_polar_cap_HL'].iloc[i] = 0

            # Calculate Kl2_polar_cap
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_kl2_polar_cap[-2:])
                self.df['calculated_Kl2_polar_cap_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Kl2_polar_cap_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_kl2_polar_cap[2:])
                if math.isnan(slope):
                    self.df['calculated_Kl2_polar_cap_LR_all_points'].iloc[i] = 0
                else:
                    self.df[
                        'calculated_Kl2_polar_cap_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Kl2_polar_cap_LR_all_points'].iloc[i] = r_value*r_value

                self.df['calculated_Kl2_polar_cap_HL'].iloc[i] = (
                    math.log(y_kl2_polar_cap[-1] / y_kl2_polar_cap[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Kl2_polar_cap_LR'].iloc[i] = 0
                self.df['r2value_Kl2_polar_cap_LR'].iloc[i] = 0
                self.df['calculated_Kl2_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl2_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl2_polar_cap_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Kl2_polar_cap_LR'].iloc[i] = 0
                self.df['r2value_Kl2_polar_cap_LR'].iloc[i] = 0
                self.df['calculated_Kl2_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['r2value_Kl2_polar_cap_LR_all_points'].iloc[i] = 0
                self.df['calculated_Kl2_polar_cap_HL'].iloc[i] = 0

            # Calculate Khc
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_khc[-2:])
                self.df['calculated_Khc_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Khc_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_khc[2:])
                if math.isnan(slope):
                    self.df['calculated_Khc_LR_all_points'].iloc[i] = 0
                else:
                    self.df[
                        'calculated_Khc_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Khc_LR_all_points'].iloc[i] = r_value*r_value

                self.df['calculated_Khc_HL'].iloc[i] = (
                    math.log(y_khc[-1] / y_khc[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Khc_LR'].iloc[i] = 0
                self.df['r2value_Khc_LR'].iloc[i] = 0
                self.df['calculated_Khc_LR_all_points'].iloc[i] = 0
                self.df['r2value_Khc_LR_all_points'].iloc[i] = 0
                self.df['calculated_Khc_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Khc_LR'].iloc[i] = 0
                self.df['r2value_Khc_LR'].iloc[i] = 0
                self.df['calculated_Khc_LR_all_points'].iloc[i] = 0
                self.df['r2value_Khc_LR_all_points'].iloc[i] = 0
                self.df['calculated_Khc_HL'].iloc[i] = 0

            # Calculate Khc_45
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[-2:], log_y_khc_45[-2:])
                self.df['calculated_Khc_45_LR'].iloc[i] = slope * (-1)
                self.df['r2value_Khc_45_LR'].iloc[i] = r_value * r_value

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x[2:], log_y_khc_45[2:])
                if math.isnan(slope):
                    self.df['calculated_Khc_45_LR_all_points'].iloc[i] = 0
                else:
                    self.df[
                        'calculated_Khc_45_LR_all_points'].iloc[i] = slope*(-1)
                self.df['r2value_Khc_45_LR_all_points'].iloc[i] = r_value*r_value

                self.df['calculated_Khc_45_HL'].iloc[i] = (
                    math.log(y_khc_45[-1] / y_khc_45[-2]) / (
                        x[-1] - x[-2])) * -1

            except IndexError:
                self.df['calculated_Khc_45_LR'].iloc[i] = 0
                self.df['r2value_Khc_45_LR'].iloc[i] = 0
                self.df['calculated_Khc_45_LR_all_points'].iloc[i] = 0
                self.df['r2value_Khc_45_LR_all_points'].iloc[i] = 0
                self.df['calculated_Khc_45_HL'].iloc[i] = 0

            except ValueError:
                self.df['calculated_Khc_45_LR'].iloc[i] = 0
                self.df['r2value_Khc_45_LR'].iloc[i] = 0
                self.df['calculated_Khc_45_LR_all_points'].iloc[i] = 0
                self.df['r2value_Khc_45_LR_all_points'].iloc[i] = 0
                self.df['calculated_Khc_45_HL'].iloc[i] = 0

        # save as csv
        fname = "Lroot_calculated_kfunctions.csv"
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

    def _create_dataframe_from_Lroot_calc_kfunctions(self):
        """
        Create dataframe from content file
        """
        # Create dataframe from content of .csv file
        self.df = pd.read_csv(io.StringIO(self.content), header=0,
                              skipinitialspace=True, index_col=0)

    def wavelength_to_rgb(self, wavelength, gamma=0.8):
        ''' taken from http://www.noah.org/wiki/Wavelength_to_RGB_in_Python
        This converts a given wavelength of light to an
        approximate RGB color value. The wavelength must be given
        in nanometers in the range from 380 nm through 750 nm
        (789 THz through 400 THz).

        Based on code by Dan Bruton
        http://www.physics.sfasu.edu/astro/color/spectra.html
        Additionally alpha value set to 0.5 outside range
        '''
        wavelength = float(wavelength)
        if wavelength >= 380 and wavelength <= 750:
            A = 1.
        else:
            A = 0.5
        if wavelength < 380:
            wavelength = 380.
        if wavelength > 750:
            wavelength = 750.
        if wavelength >= 380 and wavelength <= 440:
            attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
            R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
            G = 0.0
            B = (1.0 * attenuation) ** gamma
        elif wavelength >= 440 and wavelength <= 490:
            R = 0.0
            G = ((wavelength - 440) / (490 - 440)) ** gamma
            B = 1.0
        elif wavelength >= 490 and wavelength <= 510:
            R = 0.0
            G = 1.0
            B = (-(wavelength - 510) / (510 - 490)) ** gamma
        elif wavelength >= 510 and wavelength <= 580:
            R = ((wavelength - 510) / (580 - 510)) ** gamma
            G = 1.0
            B = 0.0
        elif wavelength >= 580 and wavelength <= 645:
            R = 1.0
            G = (-(wavelength - 645) / (645 - 580)) ** gamma
            B = 0.0
        elif wavelength >= 645 and wavelength <= 750:
            attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
            R = (1.0 * attenuation) ** gamma
            G = 0.0
            B = 0.0
        else:
            R = 0.0
            G = 0.0
            B = 0.0
        return (R, G, B, A)

    def plot_irradiances_matplotlib(self, has_show=False):
        """
        Plot calculated Irradiances from .csv file in Matplotlib

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.
        """
        mplstyle.use(['ggplot'])

        # plot of calculated_Ed for each lambda in function of depth
        # in matplotlib
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
        fig.subplots_adjust(right=0.8)
        fig.suptitle("Calculated Irradiances", fontsize=12)

        for i, df in self.df.groupby(['lambda']):

            lmbda = f'lambda: {i}'
            color = self.wavelength_to_rgb(wavelength=i)

            ax1.invert_yaxis()
            ax1.set_xlabel('Irradiance Ed (W/m^2 nm)', fontsize=8)
            ax1.set_ylabel('depth (m)', fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.plot(
                df['calculated_Ed'].iloc[1:], df['depth'].iloc[1:],
                label=lmbda, color=color)[0]
            ax1.set_title('calculated_Ed', size=10)

            ax2.invert_yaxis()
            ax2.set_xlabel('Irradiance Eu (W/m^2 nm)', fontsize=8)
            ax2.set_ylabel('depth (m)', fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.plot(
                df['calculated_Eu'].iloc[1:], df['depth'].iloc[1:],
                label=lmbda, color=color)[0]
            ax2.set_title('calculated_Eu', size=10)

            ax3.invert_yaxis()
            ax3.set_xlabel('Irradiance El1 (W/m^2 nm)', fontsize=8)
            ax3.set_ylabel('depth (m)', fontsize=8)
            ax3.grid(True, alpha=0.3)
            ax3.plot(
                df['calculated_El1'].iloc[1:], df['depth'].iloc[1:],
                label=lmbda, color=color)[0]
            ax3.set_title('calculated_El1', size=10)

            ax4.invert_yaxis()
            ax4.set_xlabel('Irradiance El2 (W/m^2 nm)', fontsize=8)
            ax4.set_ylabel('depth (m)', fontsize=8)
            ax4.grid(True, alpha=0.3)
            ax4.plot(
                df['calculated_El2'].iloc[1:], df['depth'].iloc[1:],
                label=lmbda, color=color)[0]
            ax4.set_title('calculated_El2', size=10)

        handles, labels = ax2.get_legend_handles_labels()

        # Create the legend
        fig.legend(
            handles, labels,
            bbox_to_anchor=(1.0, 0.5),
            loc='center right',
            title="wavelength",
            borderaxespad=0.5,
            fontsize=8
            )

        fig.tight_layout(rect=[0, 0.03, 0.80, 0.95])

        if not os.path.exists("images/matplotlib"):
            os.mkdir("images/matplotlib")

        plt.savefig(
            fname="images/matplotlib/calculated_irradiances.svg",
            )

        if has_show is True:
            plt.show()

    def plot_irradiances_plotly(self, has_show=False):
        """
        calculated Irradiances from .csv file in Plotly

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.

        """
        # plot of calculated_Ed for each lambda in function of depth in plotly
        # Initialize figure with subplots
        fig = make_subplots(
            rows=4, cols=2,
            column_widths=[0.5, 0.5],
            row_heights=[0.25, 0.25, 0.25, 0.25],
            subplot_titles=("calculated_Ed", 
                            "calculated_Eu", 
                            "calculated_El1_no_polar_cap",
                            "calculated_El2_no_polar_cap",
                            "calculated_El1_polar_cap",
                            "calculated_El2_polar_cap",
                            "calculated_Ehc",
                            "calculated_Ehc_45",
                            ))

        for i, df in self.df.groupby(['lambda']):
            lmbda = f'lambda: {i}'
            color = "rgba" + str(self.wavelength_to_rgb(wavelength=i))

            # Add scatter plot of irradiances
            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Ed'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    marker=dict(color=color),
                    text=df['calculated_Ed'].iloc[1:]),
                row=1, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Eu'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Eu'].iloc[1:]),
                row=1, col=2
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_El1_no_polar_cap'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_El1_no_polar_cap'].iloc[1:]),
                row=2, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_El2_no_polar_cap'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_El2_no_polar_cap'].iloc[1:]),
                row=2, col=2
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_El1_polar_cap'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_El1_polar_cap'].iloc[1:]),
                row=3, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_El2_polar_cap'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_El2_polar_cap'].iloc[1:]),
                row=3, col=2
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Ehc'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Ehc'].iloc[1:]),
                row=4, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Ehc_45'].iloc[1:],
                    y=df['depth'].iloc[1:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Ehc_45'].iloc[1:]),
                row=4, col=2
                )

        # Update xaxis properties
        fig.update_xaxes(
            title_text="Irradiance Ed (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=1, col=1)
        fig.update_xaxes(
            title_text="Irradiance Eu (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=1, col=2)
        fig.update_xaxes(
            title_text="Irradiance El1 polar cap (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=2, col=1)
        fig.update_xaxes(
            title_text="Irradiance El2 polar cap (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=2, col=2)
        fig.update_xaxes(
            title_text="Irradiance El1 no polar cap (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=3, col=1)
        fig.update_xaxes(
            title_text="Irradiance El2 no polar cap (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=3, col=2)
        fig.update_xaxes(
            title_text="Irradiance Ehc (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=4, col=1)
        fig.update_xaxes(
            title_text="Irradiance Ehc 45 (W/m^2 nm)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=4, col=2)

        # Update yaxis properties
        fig.update_yaxes(
            title_text='depth (m)',
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            autorange='reversed')

        # Update title and height
        fig.update_layout(
            title_text="<b>Calculated Irradiances</b>",
            title_font=dict(size=16),
            title=dict(
                y=0.97,
                x=0.5,
                xanchor='center',
                yanchor="top"),
            legend_title='<b> wavelength </b>',
            legend=dict(
                traceorder="normal",
                y=1,
                x=1.1,
                yanchor="top",
                font=dict(
                    family="sans-serif",
                    size=9,
                    color="black"
                ),
            )
        )

        fig.update_layout(height=1920, width=1600)

        for i in fig['layout']['annotations']:
            i['font'] = dict(size=12,color='#000000')

        """ fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    active=0,
                    x=0.57,
                    y=1.2,
                    buttons=list([
                        dict(label="1m depth",
                        method="update",
                        args=[{"visible": [True, False, True, False]},
                                {"title": "Yahoo",
                                    "annotations": []}]),
                        dict(label="2m depth",
                            method="update",
                            args=[{"visible": [True, True, False, False]},
                                {"title": "Yahoo High",
                                    "annotations": 10}]),
                        dict(label="5m depth",
                            method="update",
                            args=[{"visible": [False, False, True, True]},
                                {"title": "Yahoo Low",
                                    "annotations": 20}]),
                        dict(label="all depth",
                            method="update",
                            args=[{"visible": [True, True, True, True]},
                                {"title": "Yahoo",
                                    "annotations": 30}]),
                    ]),
                )
            ]) """
        

        if has_show is True:
            fig.show(config={'showLink': True})

        if not os.path.exists("images/plotly"):
            os.mkdir("images/plotly")
        # fig.write_image("images/plotly/calculated_irradiances.svg")
        fig.write_html("images/plotly/calculated_irradiances.html")

    def plot_kfunctionsLR_matplotlib(self, has_show=False):
        """
        Plot kfunctions calculated as Linear Regression
        from .csv file in Matplotlib

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.

        """
        mplstyle.use(['ggplot'])

        # plot of calculated_Ed for each lambda in function of depth
        # in matplotlib
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
        fig.subplots_adjust(right=0.8)
        fig.suptitle("Calculated kfunctions LR", fontsize=12)

        for i, df in self.df.groupby(['lambda']):

            lmbda = f'lambda: {i}'
            color = self.wavelength_to_rgb(wavelength=i)

            ax1.invert_yaxis()
            ax1.set_xlabel('calculated kfunction Kd (1/meter)', fontsize=8)
            ax1.set_ylabel('depth (m)', fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.plot(
                df['calculated_Kd_LR'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax1.set_title('calculated_Kd_LR', size=10)

            ax2.invert_yaxis()
            ax2.set_xlabel('calculated kfunction Ku (1/meter)', fontsize=8)
            ax2.set_ylabel('depth (m)', fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.plot(
                df['calculated_Ku_LR'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax2.set_title('calculated_Ku_LR', size=10)

            ax3.invert_yaxis()
            ax3.set_xlabel('calculated kfunction Kl1 (1/meter)', fontsize=8)
            ax3.set_ylabel('depth (m)', fontsize=8)
            ax3.grid(True, alpha=0.3)
            ax3.plot(
                df['calculated_Kl1_LR'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax3.set_title('calculated_Kl1_LR', size=10)

            ax4.invert_yaxis()
            ax4.set_xlabel('calculated kfunction Kl2 (1/meter)', fontsize=8)
            ax4.set_ylabel('depth (m)', fontsize=8)
            ax4.grid(True, alpha=0.3)
            ax4.plot(
                df['calculated_Kl2_LR'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax4.set_title('calculated_Kl2_LR', size=10)

        handles, labels = ax2.get_legend_handles_labels()

        # Create the legend
        fig.legend(
            handles, labels,
            bbox_to_anchor=(1.0, 0.5),
            loc='center right',
            title="wavelength",
            borderaxespad=0.5,
            fontsize=8
            )

        fig.tight_layout(rect=[0, 0.03, 0.80, 0.95])

        if not os.path.exists("images/matplotlib"):
            os.mkdir("images/matplotlib")

        plt.savefig(
            fname="images/matplotlib/calculated_kfunctions_LR.svg",
            )

        if has_show is True:
            plt.show()

    def plot_kfunctionsLR_plotly(self, has_show=False):
        """
        Plot kfunctions calculated as Linear Regression
        from .csv file in Plotly

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.

        """
        # plot of calculated_Kfunctions for each lambda in function of depth in plotly
        # Initialize figure with subplots

        fig = make_subplots(
            rows=4, cols=2,
            column_widths=[0.5, 0.5],
            row_heights=[0.25, 0.25, 0.25, 0.25],
            subplot_titles=(
                "calculated_Kd_LR",
                "calculated_Ku_LR",
                "calculated_Kl1_no_polar_cap_LR", 
                "calculated_Kl2_no_polar_cap_LR",
                "calculated_Kl1_polar_cap_LR", 
                "calculated_Kl2_polar_cap_LR",
                "calculated_Khc_LR", 
                "calculated_Khc_45_LR"))

        for i, df in self.df.groupby(['lambda']):
            lmbda = f'lambda: {i}'
            color = "rgba" + str(self.wavelength_to_rgb(wavelength=i))

            # Add scatter plot of irradiances
            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kd_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    marker=dict(color=color),
                    text=df['calculated_Kd_LR'].iloc[2:]),
                row=1, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Ku_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Ku_LR'].iloc[2:]),
                row=1, col=2
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kl1_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Kl1_LR'].iloc[2:]),
                row=2, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kl2_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Kl2_LR'].iloc[2:]),
                row=2, col=2
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kl1_polar_cap_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Kl1_polar_cap_LR'].iloc[2:]),
                row=3, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kl2_polar_cap_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Kl2_polar_cap_LR'].iloc[2:]),
                row=3, col=2
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Khc_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Khc_LR'].iloc[2:]),
                row=4, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Khc_45_LR'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Khc_45_LR'].iloc[2:]),
                row=4, col=2
                )

        # Update xaxis properties
        fig.update_xaxes(
            title_text="calculated kfunction Kd (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=1, col=1)
        fig.update_xaxes(
            title_text="calculated kfunction Ku (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=1, col=2)
        fig.update_xaxes(
            title_text="calculated kfunction Kl1 (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=2, col=1)
        fig.update_xaxes(
            title_text="calculated kfunction Kl2 (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=2, col=2)
        fig.update_xaxes(
            title_text="calculated kfunction Kl1 polar cap (1/meter))",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=3, col=1)
        fig.update_xaxes(
            title_text="calculated kfunction Kl2 polar cap (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=3, col=2)
        fig.update_xaxes(
            title_text="calculated kfunction Khc (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=4, col=1)
        fig.update_xaxes(
            title_text="calculated kfunction Khc 45 (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=4, col=2)

        # Update yaxis properties
        fig.update_yaxes(
            title_text='depth (m)',
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            autorange='reversed')

        # Update title and height
        fig.update_layout(
            title_text="<b>Calculated kfunctions LR</b>",
            title_font=dict(size=16),
            title=dict(
                y=0.97,
                x=0.5,
                xanchor='center',
                yanchor="top"),
            legend_title='<b> Wavelength </b>',
            legend=dict(
                traceorder="normal",
                y=1,
                x=1.1,
                yanchor="top",
                font=dict(
                    family="sans-serif",
                    size=9,
                    color="black"
                ),
            )
        )

        fig.update_layout(height=1920, width=1600)

        for i in fig['layout']['annotations']:
            i['font'] = dict(size=12,color='#000000')

        if has_show is True:
            fig.show(config={'showLink': True})

        if not os.path.exists("images/plotly"):
            os.mkdir("images/plotly")
        # fig.write_image("images/plotly/calculated_kfunctions_LR.svg")
        fig.write_html("images/plotly/calculated_kfunctions_LR.html")

    def plot_calculated_Kd_LR_all_points_matplotlib(self, has_show=False):
        """
        Plot kfunctions calculated as Linear Regression with all points
        from .csv file in Matplotlib

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.

        """
        mplstyle.use(['ggplot'])

        # plot of calculated_Ed for each lambda in function of depth
        # in matplotlib
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
        fig.subplots_adjust(right=0.8)
        fig.suptitle("Calculated kfunctions LR all points", fontsize=12)

        for i, df in self.df.groupby(['lambda']):

            lmbda = f'lambda: {i}'
            color = self.wavelength_to_rgb(wavelength=i)

            ax1.invert_yaxis()
            ax1.set_xlabel('calculated kfunction Kd (1/meter)', fontsize=8)
            ax1.set_ylabel('depth (m)', fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.plot(
                df['calculated_Kd_LR_all_points'].iloc[3:],
                df['depth'].iloc[3:],
                label=lmbda, color=color)[0]
            ax1.set_title('calculated_Kd_LR_all_points', size=10)

            ax2.invert_yaxis()
            ax2.set_xlabel('calculated kfunction Ku (1/meter)', fontsize=8)
            ax2.set_ylabel('depth (m)', fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.plot(
                df['calculated_Ku_LR_all_points'].iloc[3:],
                df['depth'].iloc[3:],
                label=lmbda, color=color)[0]
            ax2.set_title('calculated_Ku_LR_all_points', size=10)

            ax3.invert_yaxis()
            ax3.set_xlabel('calculated kfunction Kl1 (1/meter)', fontsize=8)
            ax3.set_ylabel('depth (m)', fontsize=8)
            ax3.grid(True, alpha=0.3)
            ax3.plot(
                df['calculated_Kl1_LR_all_points'].iloc[3:],
                df['depth'].iloc[3:],
                label=lmbda, color=color)[0]
            ax3.set_title('calculated_Kl1_LR_all_points', size=10)

            ax4.invert_yaxis()
            ax4.set_xlabel('calculated kfunction Kl2 (1/meter)', fontsize=8)
            ax4.set_ylabel('depth (m)', fontsize=8)
            ax4.grid(True, alpha=0.3)
            ax4.plot(
                df['calculated_Kl2_LR_all_points'].iloc[3:],
                df['depth'].iloc[3:],
                label=lmbda, color=color)[0]
            ax4.set_title('calculated_Kl2_LR_all_points', size=10)

        handles, labels = ax2.get_legend_handles_labels()

        # Create the legend
        fig.legend(
            handles, labels,
            bbox_to_anchor=(1.0, 0.5),
            loc='center right',
            title="wavelength",
            borderaxespad=0.5,
            fontsize=8
            )

        fig.tight_layout(rect=[0, 0.03, 0.80, 0.95])

        if not os.path.exists("images/matplotlib"):
            os.mkdir("images/matplotlib")

        plt.savefig(
            fname="images/matplotlib/calculated_kfunctions_LR_all_points.svg",
            )

        if has_show is True:
            plt.show()

    def plot_calculated_Kd_LR_all_points_plotly(self, has_show=False):
        """
        Plot kfunctions calculated as Linear Regression with all points
        from .csv file in Plotly

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.

        """
        # plot of calculated_kfunctions for each lambda in function of depth in plotly
        # Initialize figure with subplots
        fig = make_subplots(
            rows=4, cols=2,
            column_widths=[0.5, 0.5],
            row_heights=[0.25, 0.25, 0.25, 0.25],
            subplot_titles=(
                "calculated_Kd_LR_all_points",
                "calculated_Ku_LR_all_points",
                "calculated_Kl1_LR_all_points",
                "calculated_Kl2_LR_all_points",
                "calculated_Kl1_polar_cap_LR_all_points",
                "calculated_Kl2_polar_cap_LR_all_points",
                "calculated_Khc_LR_all_points",
                "calculated_Khc_45_LR_all_points"
               ))
        depth = 9
        lmbd_list = [460.0, 480.0, 500.0, 520.0, 540.0, 560.0,
                     580.0, 600.0, 620.0, 640.0]

        for i, df in self.df.groupby(['lambda']):
            if float(i) in lmbd_list:
                lmbda = f'lambda: {i}'
                color = "rgba" + str(self.wavelength_to_rgb(wavelength=i))

                # Add scatter plot of irradiances
                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Kd_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        marker=dict(color=color),
                        text=df['calculated_Kd_LR_all_points'].iloc[3:depth]),
                    row=1, col=1
                    )

                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Ku_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        showlegend=False,
                        marker=dict(color=color),
                        text=df['calculated_Ku_LR_all_points'].iloc[3:depth]),
                    row=1, col=2
                    )

                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Kl1_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        showlegend=False,
                        marker=dict(color=color),
                        text=df['calculated_Kl1_LR_all_points'].iloc[3:depth]),
                    row=2, col=1
                    )

                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Kl2_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        showlegend=False,
                        marker=dict(color=color),
                        text=df['calculated_Kl2_LR_all_points'].iloc[3:depth]),
                    row=2, col=2
                    )

                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Kl1_polar_cap_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        showlegend=False,
                        marker=dict(color=color),
                        text=df['calculated_Kl1_polar_cap_LR_all_points'].iloc[3:depth]),
                    row=3, col=1
                    )

                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Kl2_polar_cap_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        showlegend=False,
                        marker=dict(color=color),
                        text=df['calculated_Kl2_polar_cap_LR_all_points'].iloc[3:depth]),
                    row=3, col=2
                    )

                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Khc_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        showlegend=False,
                        marker=dict(color=color),
                        text=df['calculated_Khc_LR_all_points'].iloc[3:depth]),
                    row=4, col=1
                    )

                fig.add_trace(
                    go.Scatter(
                        x=df['calculated_Khc_45_LR_all_points'].iloc[3:depth],
                        y=df['depth'].iloc[3:depth],
                        mode="lines",
                        legendgroup="group " + str(lmbda),
                        name=lmbda,
                        showlegend=False,
                        marker=dict(color=color),
                        text=df['calculated_Khc_45_LR_all_points'].iloc[3:depth]),
                    row=4, col=2
                    )

            # Update xaxis properties
            range_xaxis = [0,0.5]
            fig.update_xaxes(
                title_text="calculated kfunction Kd (1/meter)",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=1, col=1)
            fig.update_xaxes(
                title_text="calculated kfunction Ku (1/meter)",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=1, col=2)
            fig.update_xaxes(
                title_text="calculated kfunction Kl1 (1/meter)",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=2, col=1)
            fig.update_xaxes(
                title_text="calculated kfunction Kl2 (1/meter)",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=2, col=2)
            fig.update_xaxes(
                title_text="calculated kfunction Kl1 polar cap (1/meter))",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=3, col=1)
            fig.update_xaxes(
                title_text="calculated kfunction Kl2 polar cap (1/meter)",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=3, col=2)
            fig.update_xaxes(
                title_text="calculated kfunction Khc (1/meter)",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=4, col=1)
            fig.update_xaxes(
                title_text="calculated kfunction Khc 45 (1/meter)",
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                range=range_xaxis,
                row=4, col=2)

            # Update yaxis properties
            fig.update_yaxes(
                title_text='depth (m)',
                title_font=dict(size=12),
                ticklen=5,
                zeroline=False,
                autorange='reversed')

            # Update title and height
            fig.update_layout(
                title_text="<b>Calculated kfunctions LR all points</b>",
                title_font=dict(size=16),
                title=dict(
                    y=0.97,
                    x=0.5,
                    xanchor='center',
                    yanchor="top"),
                legend_title='<b> Wavelength </b>',
                legend=dict(
                    traceorder="normal",
                    y=1,
                    x=1.1,
                    yanchor="top",
                    font=dict(
                        family="sans-serif",
                        size=9,
                        color="black"
                    ),
                )
            )

            fig.update_layout(height=1920, width=1600)
        
        if has_show is True:
            fig.show(config={'showLink': True})

        if not os.path.exists("images/plotly"):
            os.mkdir("images/plotly")
        """ fig.write_image(
            "images/plotly/calculated_kfunctions_LR_all_points.svg") """
        fig.write_html(
            "images/plotly/calculated_kfunctions_LR_all_points.html")

    def plot_calculated_Kd_HL_matplotlib(self, has_show=False):
        """
        Plot kfunctions calculated as Hydrolight
        from .csv file in Matplotlib

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.

        """
        mplstyle.use(['ggplot'])

        # plot of calculated_Ed for each lambda in function of depth
        # in matplotlib
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
        fig.subplots_adjust(right=0.8)
        fig.suptitle("Calculated kfunctions HL", fontsize=12)

        for i, df in self.df.groupby(['lambda']):

            lmbda = f'lambda: {i}'
            color = self.wavelength_to_rgb(wavelength=i)

            ax1.invert_yaxis()
            ax1.set_xlabel('calculated kfunction Kd (1/meter)', fontsize=8)
            ax1.set_ylabel('depth (m)', fontsize=8)
            ax1.grid(True, alpha=0.3)
            ax1.plot(
                df['calculated_Kd_HL'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax1.set_title('calculated_Kd_HL', size=10)

            ax2.invert_yaxis()
            ax2.set_xlabel('calculated kfunction Ku (1/meter)', fontsize=8)
            ax2.set_ylabel('depth (m)', fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.plot(
                df['calculated_Ku_HL'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax2.set_title('calculated_Ku_HL', size=10)

            ax3.invert_yaxis()
            ax3.set_xlabel('calculated kfunction Kl1 (1/meter)', fontsize=8)
            ax3.set_ylabel('depth (m)', fontsize=8)
            ax3.grid(True, alpha=0.3)
            ax3.plot(
                df['calculated_Kl1_HL'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax3.set_title('calculated_Kl1_HL', size=10)

            ax4.invert_yaxis()
            ax4.set_xlabel('calculated kfunction Kl2 (1/meter)', fontsize=8)
            ax4.set_ylabel('depth (m)', fontsize=8)
            ax4.grid(True, alpha=0.3)
            ax4.plot(
                df['calculated_Kl2_HL'].iloc[2:], df['depth'].iloc[2:],
                label=lmbda, color=color)[0]
            ax4.set_title('calculated_Kl2_HL', size=10)

        handles, labels = ax2.get_legend_handles_labels()

        # Create the legend
        fig.legend(
            handles, labels,
            bbox_to_anchor=(1.0, 0.5),
            loc='center right',
            title="wavelength",
            borderaxespad=0.5,
            fontsize=8
            )

        fig.tight_layout(rect=[0, 0.03, 0.80, 0.95])

        if not os.path.exists("images/matplotlib"):
            os.mkdir("images/matplotlib")

        plt.savefig(
            fname="images/matplotlib/calculated_kfunctions_HL.svg",
            )

        if has_show is True:
            plt.show()

    def plot_calculated_Kd_HL_plotly(self, has_show=False):
        """
        Plot kfunctions calculated as Linear Regression with all points
        from .csv file in Plotly

        Parameters
        ----------
            has_show: Boolean
                Flag to show the plot. By default, False.

        """
        # plot of calculated_Ed for each lambda in function of depth in plotly
        # Initialize figure with subplots
        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.5, 0.5],
            row_heights=[0.5, 0.5],
            subplot_titles=("calculated_Kd_HL",
                            "calculated_Ku_HL",
                            "calculated_Kl1_HL",
                            "calculated_Kl2_HL"))

        for i, df in self.df.groupby(['lambda']):
            lmbda = f'lambda: {i}'
            color = "rgba" + str(self.wavelength_to_rgb(wavelength=i))

            # Add scatter plot of irradiances
            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kd_HL'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    marker=dict(color=color),
                    text=df['calculated_Kd_HL'].iloc[2:]),
                row=1, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Ku_HL'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Ku_HL'].iloc[2:]),
                row=1, col=2
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kl1_HL'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Kl1_HL'].iloc[2:]),
                row=2, col=1
                )

            fig.add_trace(
                go.Scatter(
                    x=df['calculated_Kl2_HL'].iloc[2:],
                    y=df['depth'].iloc[2:],
                    mode="lines",
                    legendgroup="group " + str(lmbda),
                    name=lmbda,
                    showlegend=False,
                    marker=dict(color=color),
                    text=df['calculated_Kl2_HL'].iloc[2:]),
                row=2, col=2
                )

        # Update xaxis properties
        fig.update_xaxes(
            title_text="calculated kfunction Kd (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=1, col=1)
        fig.update_xaxes(
            title_text="calculated kfunction Ku (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=1, col=2)
        fig.update_xaxes(
            title_text="calculated kfunction Kl1 (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=2, col=1)
        fig.update_xaxes(
            title_text="calculated kfunction Kl2 (1/meter)",
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            row=2, col=2)

        # Update yaxis properties
        fig.update_yaxes(
            title_text='depth (m)',
            title_font=dict(size=12),
            ticklen=5,
            zeroline=False,
            autorange='reversed')

        # Update title and height
        fig.update_layout(
            title_text="<b>Calculated kfunctions LH</b>",
            title_font=dict(size=16),
            title=dict(
                y=0.97,
                x=0.5,
                xanchor='center',
                yanchor="top"),
            legend_title='<b> Wavelength </b>',
            legend=dict(
                traceorder="normal",
                y=1,
                x=1.1,
                yanchor="top",
                font=dict(
                    family="sans-serif",
                    size=9,
                    color="black"
                ),
            )
        )

        if has_show is True:
            fig.show(config={'showLink': True})

        if not os.path.exists("images/plotly"):
            os.mkdir("images/plotly")
        fig.write_image("images/plotly/calculated_kfunctions_LH.svg")
        fig.write_html("images/plotly/calculated_kfunctions_LH.html")

    def animated_loading(self, process_name=""):
        chars = r"/—\|"
        for char in chars:
            sys.stdout.write('\r'+f'{process_name} - Loading...'+char)
            time.sleep(.1)
            sys.stdout.flush()


if __name__ == "__main__":

    prf = ProcessIrradFile()
    """ prf.open_file()
    prf.create_dataframe_from_Lroot_calc_irrad()
    prf.calculate_kfunctions() """

    # Flag to show or hide plot
    has_show = False

    prf.open_file(
        file_name="Lroot_calculated_kfunctions.csv",
        path_file="files/csv")
    prf._create_dataframe_from_Lroot_calc_kfunctions()

    # prf.plot_irradiances_matplotlib(has_show=has_show)
    # prf.plot_irradiances_plotly(has_show=has_show)

    # prf.plot_kfunctionsLR_matplotlib(has_show=has_show)
    # prf.plot_kfunctionsLR_plotly(has_show=has_show)

    # prf.plot_calculated_Kd_LR_all_points_matplotlib(has_show=has_show)
    prf.plot_calculated_Kd_LR_all_points_plotly(has_show=has_show)

    # prf.plot_calculated_Kd_HL_matplotlib(has_show=has_show)
    # to do
    # prf.plot_calculated_Kd_HL_plotly(has_show=has_show)
