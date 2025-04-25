# Configuration Information
Here is the information about the configuration parameters.  
## Parameters
We need to configure 14 parameters for the LIMBO design.
1. `fs`: this sets the sample frequency.  
    The valid options are:
    * 500  
2. `snap_id`: this sets the id number in the packets.  
    We use `2` here.  
    **Note:** this could be any 8bit number.
3. `adc_gain`: this sets the gain value in the ADC.
    TODO: add the reasonable values here.
4. `adc_scale`: bit shift the raw adc data.  
    The valid range is `0 - 4`.
5. `adc_delays`: set the digital delay for each lane.  
    The valid range is `5 - 4095`.
6. `fft_shift`: fft shift value set for the FFT block.  
    The valid range is `0 - 4095`.
7. `acc_len`: accumulation length.  
    The max value is `2**24-1`.
8. `spec_coeff`: this coeff is multiplied to the spectra data.
    The max value is `2**16-1`.
9. `data_sel`: select which `16` bits to be the output.
    * `0`: bit 15 - bit 0;
    * `1`: bit 31 - bit 16;
    * `2`: bit 47 - bit 32;
    * `3`: bit 63 - bit 48.
10. `polx_eq_coeff`: channel equalization values.  
    We could set different values for different channels.
11. `adc_ref`: adc reference clock.
    Valid options:
    * `10`: it means the adc reference clock is 10MHz;
    * `None`: it means the sampling clock is connected to the SNAP directly.
