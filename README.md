# Calculate Kfunctions from Lroot_calculated_irradiances.csv file

This is a Python script to obtain the diffuse attenuation coefficients (Kfunctions) from Lroot_calculated_irradiances.csv file. 
Source: https://github.com/Carlos-Rodero/calculate-irradiances-Hydrolight

This script calculate Kd as the diffuse attenuation coefficient of downwelling irradiance, Ku as the diffuse attenuation coefficient of upwelling irradiance and Kl as the diffuse attenuation coefficient of lateral-welling irradiance.
It calculates Kfunctions in 3 different ways:
- as a negative of the slope of linear regression between lnE (y) and depth (x) in the last two dephts (z2 and z1)
- as a negative of the slope of linear regression between lnE (y) and depth (x) in all points until last depth
- as Hydrolight does: as a logarithmic derivative (see Hydrolight Users Guide) 

## Instructions

- Copy your Lroot_calculated_irradiances.csv file obtained in this script:
https://github.com/Carlos-Rodero/calculate-irradiances-Hydrolight 
inside the files/raw folder
- Results appear in files/csv folder
- Plots appear in images/matplotlib or images/plotly folder
