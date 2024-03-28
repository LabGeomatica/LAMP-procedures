# LAMP_procedures

Program name: LAMP procedures

Created on Fri Jun  3 14:21:52 2022

@authors: Stefania Viaggio, Estelle Stefanini, Rossella Bovolenta, Bianca Federici

Estelle was student at the National School of Geographic Sciences (ENSG - France); she wrote the initial version of the codes in python during her internship in the Geomatic Lab at the University of Genova (UniGe - Italy)

Stefania was PhD candidate in the Geomatic Lab at the University of Genova (UniGe - It); she define the procedure and improved the codes. 

They both worked under the supervision of Profs Rossella Bovolenta and Bianca Federici, at UniGe. 

Copyright (C) 2022 Viaggio, Stefanini, Bovolenta, Federici

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses/.

Geotechnical and Geomatic researchers of the University of Genoa developed the LAMP (Landslide Monitoring and Predicting) system. This system is composed by two automatic procedures: (1) IHG - Integrated Hydrological-Geotechnical model, which, fed by a sensor network, provides landslide susceptibility maps triggered by changes in groundwater levels; (ii) SAC - Soil Apparent Cohesion model, which allows the estimate of the soil shear strength starting from soil moisture monitoring data, so to estimate landslide susceptibility induced by changes in soil saturation conditions.

(i) IHG.py -> A physically based Integrated Hydrological and Geotechnical (IHG) model was implemented in GIS environment to effectively analyse areas of a few square kilometres, typically at a scale of 1:5.000. Referring to each volume element in which the whole mass under study is discretized, a simplified hydrological soil-water balance and geotechnical modelling are applied in order to assess the debris and earth slide susceptibility in occasion of measured or forecasted rainfalls. The IHG procedure allows 3D modelling of landslide areas, both morphologically and with regard to geotechnical/hydrological parameters thanks to the spatialisation of input data from in situ measurements, and renders easy-to-understand results. 

(ii) SAC.py -> Considering rain-triggered shallow landslides, the stability can be markedly influenced by the propagation of the saturation front inside the unsaturated zone. Soil shear strength varies in the vadose zone depending on the type of soil and the variations of soil moisture. Monitoring of the unsaturated zone can be done by measuring volumetric water content using low-cost instrumentation (i.e. capacitive sensors) that are easy to manage and provide data in near-real time. For a proper soil moisture assessment a laboratory soil-specific calibration of the sensors is recommended. Knowing the soil water content, the suction parameter can be estimated by a Water Retention Curve (WRC), and consequently the soil shear strength in unsaturated conditions is evaluated. The automatic procedure developed in GIS environment, named assessment of Soil Apparent Cohesion (SAC), here described, allows the estimate of the soil shear strength starting from soil moisture monitoring data (from sensor networks or satellite-derived map). SAC results can be integrated into existing models for landslide susceptibility assessment and also for the emergency management.

Some significant results concerning the automatic IHG and SAC procedures, applied to landslides within the Alcotra AD-VITAM project, are presented in Stefania PhD thesis.

If you need to contact us: stefaniaviaggio at gmail.com, rossella.bovolenta at unige.it, bianca.federici at unige.it
