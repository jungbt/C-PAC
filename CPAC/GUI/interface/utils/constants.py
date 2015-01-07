def enum(**enums):
    return type('Enum', (), enums)


control = enum(CHOICE_BOX = 0, 
               TEXT_BOX = 1, 
               COMBO_BOX = 2,
               INT_CTRL = 3,
               FLOAT_CTRL = 4,
               DIR_COMBO_BOX = 5,
               CHECKLIST_BOX = 6,
               LISTBOX_COMBO = 7,
               TEXTBOX_COMBO = 8,
               CHECKBOX_GRID = 9)

dtype = enum(BOOL = 0,
             STR= 1,
             NUM= 2,
             LBOOL = 3,
             LSTR = 4,
             LNUM = 5,
             LOFL = 6,
             COMBO = 7,
             LDICT= 8 ) 


substitution_map = {'On': 1,
                    'Off': 0,
                    'On/Off': 10,
                    'ANTS & FSL': 11,
                    '3dAutoMask & BET': 12,
                    'ALFF':'alff_to_standard',
                    'ALFF (smoothed)':'alff_to_standard_smooth',
                    'ALFF (smoothed, z-score std)':'alff_to_standard_smooth_zstd',
                    'f/ALFF':'falff_to_standard',
                    'f/ALFF (smoothed)':'falff_to_standard_smooth',
                    'f/ALFF (smoothed, z-score std)':'falff_to_standard_smooth_zstd',
                    'ReHo':'reho_to_standard',
                    'ReHo (smoothed)':'reho_to_standard_smooth',
                    'ReHo (smoothed, z-score std)':'reho_to_standard_smooth_zstd',
                    'ROI Average SCA':'sca_roi_to_standard',
                    'ROI Average SCA (Fisher z-score std)':'sca_roi_to_standard_fisher_zstd',
                    'ROI Average SCA (smoothed)':'sca_roi_to_standard_smooth',
                    'ROI Average SCA (smoothed, Fisher z-score std)':'sca_roi_to_standard_smooth_fisher_zstd',
                    'Voxelwise SCA':'sca_seed_to_standard',
                    'Voxelwise SCA (Fisher z-score std)':'sca_seed_to_standard_fisher_zstd',
                    'Voxelwise SCA (smoothed)':'sca_seed_to_standard_smooth',
                    'Voxelwise SCA (smoothed, Fisher z-score std)': 'sca_seed_to_standard_smooth_fisher_zstd',
                    'Multiple Regression SCA (smoothed)':'sca_tempreg_maps_zstat_files_smooth',
                    'VMHC (Fisher z-score std)':'vmhc_fisher_zstd',
                    'VMHC z-stat (Fisher z-score std)':'vmhc_fisher_zstd_zstat_map',
                    'Network Centrality (smoothed)':'centrality_outputs_smoothed',
                    'Network Centrality (smoothed, z-score std)': 'centrality_outputs_zstd',
                    'Dual Regression':'dr_tempreg_maps_files_to_standard',
                    'Dual Regression (smoothed)':'dr_tempreg_maps_files_to_standard_smooth',
                    'Dual Regression z-stat':'dr_tempreg_maps_zstat_files_to_standard',
                    'Dual Regression z-stat (smoothed)':'dr_tempreg_maps_zstat_files_to_standard_smooth',
                    'End': 'None',
                    'ROI Average Time Series Extraction': 'roi_average',
                    'ROI Voxelwise Time Series Extraction': 'roi_voxelwise',
                   }


multiple_value_wfs = ['runAnatomicalPreprocessing',
                      'runFunctionalPreprocessing',
                      'runRegistrationPreprocessing',
                      'runRegisterFuncToMNI',
                      'runAnatomicalToFunctionalRegistration',
                      'runSegmentationPreprocessing',
                      'runNuisance',
                      'runFrequencyFiltering',
                      'runMedianAngleCorrection',
                      'runGenerateMotionStatistics',
                      'runScrubbing',
                      'runFristonModel']
