# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 14:21:52 2022

@author: Stella-Maria
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterMapLayer
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsVectorLayer, QgsVectorLayerUtils, QgsProcessingUtils, QgsMapLayer, QgsRasterLayer
import processing
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os


class DeltaC(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterEnum('type_input', 'Type of input data', options = ['raw vector data','calibrated vector data','VWC map','satellite images'], allowMultiple = False, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('a', 'a', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=10000, defaultValue=276.5))
        self.addParameter(QgsProcessingParameterNumber('b', 'b', type=QgsProcessingParameterNumber.Double, minValue=-1000, maxValue=10000, defaultValue=-87.8))
        self.addParameter(QgsProcessingParameterNumber('Gs', 'Gs', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=10000, defaultValue=2.6))
        self.addParameter(QgsProcessingParameterNumber('C', 'C', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=100, defaultValue=1.304))
        self.addParameter(QgsProcessingParameterNumber('Sand', 'Sand', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=100, defaultValue=47.9))
        self.addParameter(QgsProcessingParameterNumber('Clay', 'Clay', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=100, defaultValue=29.0))
        self.addParameter(QgsProcessingParameterNumber('tan_phi', 'tan(φ)', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.522))
        self.addParameter(QgsProcessingParameterMapLayer('Data', 'Input data',defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('teta_max', 'θmax', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=10000, defaultValue=0.478))
        self.addParameter(QgsProcessingParameterFolderDestination('Output_Folder','Folder for dowload maps'))
  
    
    def processAlgorithm(self, parameters, context, model_feedback):
        
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}
        
        folder = QgsProcessingUtils.tempFolder()
    
            
        
        ##Calcul constantes
        wmax = parameters['teta_max']/((1-parameters['teta_max'])*parameters['Gs'])
        rhod = ((1000*parameters['Gs'])/(1+wmax*parameters['Gs']))/1000
        alpha = np.exp(-2.486 + 0.025*parameters['Sand'] - 0.351*parameters['C'] - 2.617*rhod - 0.023*parameters['Clay'])
        n = np.exp(0.053 + 0.009*parameters['Sand'] - 0.013*parameters['Clay'] - 0.00015*(parameters['Sand']**2))
        teta_r = 0.015 + 0.005*parameters['Clay'] + 0.014*parameters['C']
        teta_s = 0.81 - 0.283*rhod + 0.001*parameters['Clay']
        
        s = [0.001, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5] + [5*i for i in range(1,20000)]
       
        results['wmax']=wmax
        results['ρd']=rhod
        results['α']=alpha
        results['n']=n
        results['θr']=teta_r
        results['θs']=teta_s
        
        file = open(parameters['Output_Folder'].replace('/','\\')+'\\WRC_params.txt', "w") 
        file.write('wmax = '+str(wmax)+'\n'+'ρd = '+str(rhod)+'\n'+'α = '+str(alpha)+'\n'+'n = '+str(n)+'\n'+'θr = '+str(teta_r)+'\n'+'θs = '+str(teta_s)) 
        file.close()
        
        if parameters['type_input']==0:
            data = self.parameterAsLayer(parameters, 'Data', context)
            fields = data.fields().names()
            z_value = QgsVectorLayerUtils.getValues(data, 'z_ground[c')[0]
            z_value = list(set(z_value))

           
            
            input_0 = parameters['Data']
            for i in range(len(fields)-4):
                cal = fields[i+4] + '__Calibrate'
    
                formule ='('+str(parameters['a'])+'*"'+ fields[i+4]+ '"/3+'+str(parameters['b'])+')/100'
                formule_suite = 'if('+formule+'<='+str(teta_r)+','+str(teta_r+0.001)+','+formule+')'
                alg_params = {
                    'INPUT': input_0,
                    'FIELD_NAME': cal,
                    'FIELD_TYPE': 0,  # Flottant
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 3,
                    'FORMULA': formule_suite,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs[cal] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                #results[cal] = outputs[cal]['OUTPUT']
                input_0 = outputs[cal]['OUTPUT']
                
                s_eff = fields[i+4] + '__s_eff'
                formule = '("' + cal + '"-' + str(teta_r) + ')/(' + str(parameters['teta_max']) + '-' + str(teta_r) + ')'
                alg_params = {
                    'INPUT': input_0,
                    'FIELD_NAME': s_eff,
                    'FIELD_TYPE': 0,  # Flottant
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 3,
                    'FORMULA': formule,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT  
                }
                outputs[s_eff] = processing.run('native:fieldcalculator', alg_params,  context=context, feedback=feedback, is_child_algorithm=True)
                #results[s_eff] = outputs[s_eff]['OUTPUT']
                input_0 =  outputs[s_eff]['OUTPUT']
                
                sat = fields[i+4]+'__s'
                formule = '(10/' + str(alpha) + '*10^(-2))*(((' + str(teta_s) + '-"' + cal + '")/("' + cal + '"-' + str(teta_r) + '))^(1/' + str(n) + '))'
                alg_params = {
                    'INPUT': input_0,
                    'FIELD_NAME': sat,
                    'FIELD_TYPE': 0,  # Flottant
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 3,
                    'FORMULA': formule,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT  
                }
                outputs[sat] = processing.run('native:fieldcalculator', alg_params,  context=context, feedback=feedback, is_child_algorithm=True)
                #results[sat] = outputs[sat]['OUTPUT']
                input_0 =  outputs[sat]['OUTPUT']
                
                dC = fields[i+4]+'__ΔC'
                formule = '"' + sat + '"*"' + s_eff + '"*' + str(parameters['tan_phi'])
                alg_params = {
                    'INPUT': input_0,
                    'FIELD_NAME': dC,
                    'FIELD_TYPE': 0,  # Flottant
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 3,
                    'FORMULA': formule,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
                }
                outputs[dC] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                results[dC] = outputs[dC]['OUTPUT']
                input_0 =  outputs[dC]['OUTPUT']       
                
                
                
                alg_params = {
                    'FORMATTED_VALUES': False,
                    'LAYERS': outputs[dC]['OUTPUT'],
                    'OVERWRITE': True,
                    'USE_ALIAS': False,
                    'OUTPUT': parameters['Output_Folder']+'/table.csv'
                }
                outputs['tableur'] = processing.run('native:exporttospreadsheet', alg_params, context=context, feedback=feedback, is_child_algorithm=True)



                for z in z_value:
                    selected = fields[i+4]+'__'+str(z)+'_select'
                    alg_params = {
                        'INPUT': input_0,
                        'FIELD': 'z_ground[c',
                        'METHOD': 0,  # New selection
                        'OPERATOR': 0,  # equal to
                        'VALUE': z
                    }
                    outputs[selected] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                    
                    #out_name = parameters['Output_Folder']+'/'+fields[i+4].replace('/','-')+'__Extracted_-10.shp'
                    extracted = fields[i+4]+'__'+str(z)
                    alg_params = {
                        'INPUT': input_0,
                        'OUTPUT':folder.replace('/','\\')+'\\test'+str(i)+str(z)+'.shp'
                    }
                    outputs[extracted] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                    #results[extracted]= outputs[extracted]['OUTPUT']
                    
                    
                    
                    field_number = len(fields)+(i+1)*4-1
                    int_name = fields[i+4] + '__Inter_'+str(z)
                    rect = QgsVectorLayer.extent(data)
                    extent=str(rect.xMinimum())+','+str(rect.xMaximum())+','+str(rect.yMinimum())+','+str(rect.yMaximum())+' ['+str(QgsVectorLayer.sourceCrs(data))[-10:-1]+']'
                    int_data ='{}::~::{}::~::{}::~::{}'.format(folder.replace('/','\\')+'\\test'+str(i)+str(z)+'.shp', '0', str(field_number), '0')
                    out_name = parameters['Output_Folder']+'\\'+fields[i+4].replace('/','-')+'__Inter_'+str(z)+'.tif'
                    alg_params = { 
                        'EXTENT' : extent, 
                        'INTERPOLATION_DATA' : int_data, 
                        'METHOD' : 0, 
                        'OUTPUT' : out_name, 
                        'PIXEL_SIZE' : 5 
                    }
                    outputs[int_name] = processing.run('qgis:tininterpolation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                    results[int_name] = outputs[int_name]['OUTPUT']
                    
        
        
        
        if parameters['type_input']==1:
            data = self.parameterAsLayer(parameters, 'Data', context)
            fields = data.fields().names()
            z_value = QgsVectorLayerUtils.getValues(data, 'z_ground[c')[0]
            z_value = list(set(z_value))
            
    
            
           
            
            input_0 = parameters['Data']
            for i in range(len(fields)-4):
                s_eff = fields[i+4] + '__s_eff'
                formule = '("' + fields[i+4] + '"-' + str(teta_r) + ')/(' + str(parameters['teta_max']) + '-' + str(teta_r) + ')'
                alg_params = {
                    'INPUT': input_0,
                    'FIELD_NAME': s_eff,
                    'FIELD_TYPE': 0,  # Flottant
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 3,
                    'FORMULA': formule,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT  
                }
                outputs[s_eff] = processing.run('native:fieldcalculator', alg_params,  context=context, feedback=feedback, is_child_algorithm=True)
                #results[s_eff] = outputs[s_eff]['OUTPUT']
                input_0 =  outputs[s_eff]['OUTPUT']
                
                sat = fields[i+4]+'__s'
                formule = '(10/' + str(alpha) + '*10^(-2))*(((' + str(teta_s) + '-"' + fields[i+4] + '")/("' + fields[i+4] + '"-' + str(teta_r) + '))^(1/' + str(n) + '))'
                alg_params = {
                    'INPUT': input_0,
                    'FIELD_NAME': sat,
                    'FIELD_TYPE': 0,  # Flottant
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 3,
                    'FORMULA': formule,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT  
                }
                outputs[sat] = processing.run('native:fieldcalculator', alg_params,  context=context, feedback=feedback, is_child_algorithm=True)
                #results[sat] = outputs[sat]['OUTPUT']
                input_0 =  outputs[sat]['OUTPUT']
                
                dC = fields[i+4]+'__ΔC'
                formule = '"' + sat + '"*"' + s_eff + '"*' + str(parameters['tan_phi'])
                alg_params = {
                    'INPUT': input_0,
                    'FIELD_NAME': dC,
                    'FIELD_TYPE': 0,  # Flottant
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 3,
                    'FORMULA': formule,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
                }
                outputs[dC] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                results[dC] = outputs[dC]['OUTPUT']
                input_0 =  outputs[dC]['OUTPUT']   
                
                
                alg_params = {
                    'FORMATTED_VALUES': False,
                    'LAYERS': outputs[dC]['OUTPUT'],
                    'OVERWRITE': True,
                    'USE_ALIAS': False,
                    'OUTPUT': parameters['Output_Folder']+'/table.csv'
                }
                outputs['tableur'] = processing.run('native:exporttospreadsheet', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

                
                for z in z_value:
                    selected = fields[i+4]+'__'+str(z)+'_select'
                    alg_params = {
                        'INPUT': input_0,
                        'FIELD': 'z_ground[c',
                        'METHOD': 0,  # New selection
                        'OPERATOR': 0,  # equal to
                        'VALUE': z
                    }
                    outputs[selected] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                    
                    #out_name = parameters['Output_Folder']+'/'+fields[i+4].replace('/','-')+'__Extracted_-10.shp'
                    extracted = fields[i+4]+'__'+str(z)
                    alg_params = {
                        'INPUT': input_0,
                        'OUTPUT':folder.replace('/','\\')+'\\test'+str(i)+str(z)+'.shp'
                    }
                    outputs[extracted] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                    #results[extracted]= outputs[extracted]['OUTPUT']
                    
                    
                    
                    field_number = len(fields)+(i+1)*3-1
                    int_name = fields[i+4] + '__Inter_'+str(z)
                    rect = QgsVectorLayer.extent(data)
                    extent=str(rect.xMinimum())+','+str(rect.xMaximum())+','+str(rect.yMinimum())+','+str(rect.yMaximum())+' ['+str(QgsVectorLayer.sourceCrs(data))[-10:-1]+']'
                    int_data ='{}::~::{}::~::{}::~::{}'.format(folder.replace('/','\\')+'\\test'+str(i)+str(z)+'.shp', '0', str(field_number), '0')
                    out_name = parameters['Output_Folder']+'\\'+fields[i+4].replace('/','-')+'__Inter_'+str(z)+'.tif'
                    alg_params = { 
                        'EXTENT' : extent, 
                        'INTERPOLATION_DATA' : int_data, 
                        'METHOD' : 0, 
                        'OUTPUT' : out_name, 
                        'PIXEL_SIZE' : 5 
                    }
                    outputs[int_name] = processing.run('qgis:tininterpolation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                    results[int_name] = outputs[int_name]['OUTPUT']
                    

                    
    
        if parameters['type_input']==2:
            
            data = self.parameterAsLayer(parameters, 'Data', context)
            
            formule = '('+str(parameters['a'])+'*"'+ data.name()+ '@1"/3+'+str(parameters['b'])+')/100'
            alg_params = {
                'EXPRESSION':formule,
                'LAYERS':[parameters['Data']],
                'CELLSIZE':0,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calibration']=processing.run("qgis:rastercalculator", alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['Calibration']=outputs['Calibration']['OUTPUT']
            
            cal = QgsProcessingUtils.mapLayerFromString(outputs['Calibration']['OUTPUT'], context)
            formule = '("' +QgsMapLayer.name(cal) + '@1"-' + str(teta_r) + ')/(' + str(parameters['teta_max']) + '-' + str(teta_r) + ')'
            alg_params = {
                'EXPRESSION':formule,
                'LAYERS':[parameters['Data'],cal],
                'CELLSIZE':0,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT': folder.replace('/','\\') + '\\s_eff.tif'
            }
            outputs['s_eff']=processing.run("qgis:rastercalculator", alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['s_eff']=outputs['s_eff']['OUTPUT']
            
            s_eff = QgsProcessingUtils.mapLayerFromString(outputs['s_eff']['OUTPUT'], context)
            
            out_name = parameters['Output_Folder']+'\\'+data.name().replace('/','-')+'_Suction.tif'
            formule = '(10/' + str(alpha) + '*10^(-2))*(((' + str(teta_s) + '-"' + QgsMapLayer.name(cal) + '@1")/("' +QgsMapLayer.name(cal) + '@1"-' + str(teta_r) + '))^(1/' + str(n) + '))'
            alg_params = {
                'EXPRESSION':formule,
                'LAYERS':[parameters['Data'],cal],
                'CELLSIZE':0,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT':out_name
            }
            outputs['sat']=processing.run("qgis:rastercalculator", alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['sat']=outputs['sat']['OUTPUT']
            
            
            sat = QgsProcessingUtils.mapLayerFromString(outputs['sat']['OUTPUT'], context)
            
            
            out_name = parameters['Output_Folder']+'\\'+data.name().replace('/','-')+'__Inter.tif'
            formule = '"'+  QgsMapLayer.name(sat)+'@1"*"'+ QgsMapLayer.name(s_eff)+'@1"*'+str(parameters['tan_phi'])
            alg_params = {
                'EXPRESSION':formule,
                'LAYERS':[parameters['Data'],cal,sat,s_eff],
                'CELLSIZE':0,
                'EXTENT':None,
                'CRS':None,
                'OUTPUT':out_name
            }
            outputs['Delta_C']=processing.run("qgis:rastercalculator", alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['Delta_C']=outputs['Delta_C']             

            
            
                    
        # Function to calculate teta for a list of values s given
        def calc_teta(teta_r, teta_s, alpha, n, s):
            teta = []
            for i in s:
                teta.append(teta_r + (teta_s - teta_r)/(1 + (alpha*i/10)**n))
            return teta
    
    
        # Drawing of the WRC
        plt.figure()
        plt.plot(s, calc_teta(teta_r, teta_s, alpha, n, s), 'b')
        plt.plot(s, [teta_r for i in range(len(s))], 'orange')
        plt.scatter(1, teta_s, color='black')
        plt.xscale("log")
        plt.axis([1,100000,0,0.5])
        plt.xlabel('log(s) [kPa]')
        plt.ylabel('θv [-]')
        black_patch = mpatches.Patch(color='black', label='θs')
        blue_patch = mpatches.Patch(color='blue', label='WRC')
        orange_patch = mpatches.Patch(color='orange', label='θr')
        plt.legend(handles=[black_patch, blue_patch, orange_patch])
        plt.savefig(parameters['Output_Folder']+'\\WRC.png')
        
        return results
            
    def name(self):
        return 'DeltaC'

    def displayName(self):
        return 'DeltaC'

    def createInstance(self):
        return DeltaC()
    
        