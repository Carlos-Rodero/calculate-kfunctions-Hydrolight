from calculate_kfunctions import ProcessIrradFile


if __name__ == "__main__":

    pirradf = ProcessIrradFile()

    pirradf.calc_kfunctions(file_name="Lroot_calculated_irradiances.csv")
    pirradf.plot_kfunctions(
        file_name_csv="Lroot_calculated_irradiances_calculated_kfunctions.csv")
