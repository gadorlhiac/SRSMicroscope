import yaml
formset = {}

formset['insight'] = [
        ('', 'h5:Laser Operation', ''),
        ('_emission_button', '_main_shutter_button', '_fixed_shutter_button'),
        ('', 'h5:Wavelength Selection', ''),
        ('_main_wl_label'),
        ('tune_wl_val','','tune_wl_button'),
        ('', 'h5:Laser Statistics', ''),
        ('', 'Laser State:', '_state_label', ''),
        ('_diode1_hrs_label', '', '_diode2_hrs_label'),
        ('_diode1_temp_label', '', '_diode2_temp_label'),
        ('_diode1_curr_label', '', '_diode2_curr_label'),
        ('','h5:Logs',''),
        ('_action_history', '||', '_code_history')
]
formset['stage'] = [
        ('h5:Delay Stage State:','_state_label'),
        ('', 'h5:Delay Stage Operation', ''),
        ('_home_button', '', '_disable_button', '','_enable_button'),
        ('', 'Current Position (mm):', '_pos_label'),
        ('gotopos_text', '', 'absmov_button'),
        ('Make a relative move (mm)'),
        ('_movrev_button', '', '_relmov_text', '', '_movfor_button'),
        ('', '', ''),
        ('', 'Current Velocity (mm/s):', '_vel_label'),
        ('', '_vel_text', '_vel_button'),
        ('', 'Current Acceleration (mm/s2):', '_accel_label'),
        ('', '_accel_text', '_accel_button'),
        ('_action_history')
        ]

formset['zidaq'] = [
        #('', 'h5:Connection Selectors', ''),
        #('_sigin_sele', '', '_sigout_sele'),
        #('', 'h5:Oscilloscope Trace', ''),
        #('', '_scope_viewer', ''),
        ('', 'h5:Parameter Setting', ''),
        ('tc_text', '', 'set_tc_button'),
        ('freq_text', '', 'set_freq_button'),
        ('rate_text', '', 'set_rate_button'),
        ('', 'h5:Logs', ''),
        ('_action_history')
]

formset['expmt'] = [{
            'Experiment Control: SRS (fs)': ['_expmt_panel'],
            'Laser and Delay Stage Controls': [('_insight_panel', '||', '_stage_panel')],
            'ZI Lock-in Controls': ['_zidaq_panel'],
        }]

d = yaml.dump(formset)

with open('formset.yaml', 'w') as f:
    f.write(d)