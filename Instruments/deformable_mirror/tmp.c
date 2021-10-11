
#line 8 "<root>"
typedef int16_t ViInt16;
typedef int32_t ViInt32;
typedef uint32_t ViUInt32;
typedef char ViChar;
typedef char*  ViString;

typedef float ViReal32;
typedef double ViReal64;
typedef bool ViBoolean;

typedef ViUInt32            ViObject;
typedef ViObject            ViSession;
typedef ViSession*          ViPSession;
typedef ViInt32             ViStatus;
typedef char* ViRsrc;
#line 133 "c:\program files\ivi foundation\visa\win64\include\tldfm_def.h"
typedef enum
{
   SM_Auto = 0,
   SM_Manual,

} TLDFM_Switch_Mode;

typedef enum
{
   AM_No_Lock = 0,
   AM_Exclusive_Lock = 1,
   AM_Shared_Lock =2,
} TLDFM_Access_Mode;



typedef int (
#line 4 "<root>"
*
#line 150 "c:\program files\ivi foundation\visa\win64\include\tldfm_def.h"
StatusUpdate)(ViChar[]);
#line 29 "c:\program files\ivi foundation\visa\win64\include\tldfm.h"
ViStatus  TLDFM_get_device_count (ViSession instrumentHandle ,
                                                    ViUInt32 * pDeviceCount);

 ViStatus  TLDFM_get_device_information (ViSession instrumentHandle ,
                                                          ViUInt32 deviceIndex ,
                                                          ViChar manufacturer[] ,
                                                          ViChar instrumentName[] ,
                                                          ViChar serialNumber[] ,
                                                          ViBoolean * pDeviceAvailable ,
                                                          ViChar resourceName[]);




 ViStatus  TLDFM_init (ViRsrc     resourceName ,
                                        ViBoolean  IDQuery ,
                                        ViBoolean  resetDevice ,
                                        ViPSession pInstrumentHandle);

 ViStatus  TLDFM_close (ViSession  instrumentHandle);

 ViStatus  TLDFM_reset (ViSession  instrumentHandle);

 ViStatus  TLDFM_self_test (ViSession  instrumentHandle,
                                             ViInt16*   pSelfTestResult,
                                             ViChar     selfTestMessage[]);

 ViStatus  TLDFM_error_query (ViSession  instrumentHandle,
                                               ViInt32*   pErrorCode,
                                               ViChar     errorMessage[]);

 ViStatus  TLDFM_error_message (ViSession  instrumentHandle,
                                                 ViStatus   errorCode,
                                                 ViChar     errorMessage[]);

 ViStatus  TLDFM_revision_query (ViSession  instrumentHandle,
                                                  ViChar     driverRevision[],
                                                  ViChar     firmwareRevision[]);



 ViStatus  TLDFM_set_USB_access_mode (ViSession instrumentHandle,
                                                       ViUInt32  accessMode,
                                                       ViString  requestedKey,
                                                       ViChar    accessKey[]);




 ViStatus  TLDFM_get_segment_voltage (ViSession instrumentHandle,
                                                       ViUInt32  segmentIndex,
                                                       ViReal64* pSegmentVoltage);

 ViStatus  TLDFM_set_segment_voltage (ViSession instrumentHandle,
                                                       ViUInt32  segmentIndex,
                                                       ViReal64  segmentVoltage);

 ViStatus  TLDFM_get_segment_voltages (ViSession instrumentHandle,
                                                       ViReal64  segmentVoltages[]);

 ViStatus  TLDFM_set_segment_voltages (ViSession instrumentHandle,
                                                       ViReal64  segmentVoltages[]);




 ViStatus  TLDFM_get_tilt_voltage (ViSession instrumentHandle,
                                                    ViUInt32  tiltIndex,
                                                    ViReal64* pTiltVoltage);

 ViStatus  TLDFM_set_tilt_voltage (ViSession instrumentHandle,
                                                    ViUInt32  tiltIndex,
                                                    ViReal64  tiltVoltage);

 ViStatus  TLDFM_get_tilt_voltages (ViSession instrumentHandle,
                                                     ViReal64  tiltVoltages[]);

 ViStatus  TLDFM_set_tilt_voltages (ViSession instrumentHandle,
                                                     ViReal64  tiltVoltages[]);

 ViStatus  TLDFM_set_tilt_amplitude_angle (ViSession instrumentHandle,
                                                            ViReal64  amplitute,
                                                            ViReal64  angle);





 ViStatus  TLDFM_get_voltages (ViSession instrumentHandle,
                                                ViReal64  segmentVoltages[],
                                                ViReal64  tiltVoltages[]);

 ViStatus  TLDFM_set_voltages (ViSession instrumentHandle,
                                                ViReal64  segmentVoltages[],
                                                ViReal64  tiltVoltages[]);




 ViStatus  TLDFM_get_manufacturer_name (ViSession instrumentHandle,
                                                         ViChar    manufacturerName[]);

 ViStatus  TLDFM_get_instrument_name (ViSession instrumentHandle,
                                                       ViChar    instrName[]);

 ViStatus  TLDFM_set_instrument_name (ViSession instrumentHandle,
                                                       ViChar    instrName[]);

 ViStatus  TLDFM_get_serial_Number (ViSession instrumentHandle,
                                                     ViChar    serialNumber[]);

 ViStatus  TLDFM_set_serial_number (ViSession instrumentHandle,
                                                     ViChar    serialNumber[]);

 ViStatus  TLDFM_get_user_text (ViSession instrumentHandle,
                                                 ViChar    userText[]);

 ViStatus  TLDFM_set_user_text (ViSession instrumentHandle,
                                                 ViChar    userText[]);

 ViStatus  TLDFM_update_firmware (ViSession instrumentHandle,
                                                   ViChar    firmwareFile[]);

 ViStatus  TLDFM_enable_event (ViSession instrumentHandle);

 ViStatus  TLDFM_disable_event (ViSession instrumentHandle);

 ViStatus  TLDFM_add_status_delegate (ViSession    instrumentHandle,
	                                                   StatusUpdate statusUpdateDelegate);



 ViStatus  TLDFM_get_segment_count (ViSession instrumentHandle,
                                                     ViUInt32* pSegmentCount);

 ViStatus  TLDFM_get_segment_maximum (ViSession instrumentHandle,
                                                       ViReal64* pSegmentMaximum);

 ViStatus  TLDFM_get_segment_minimum (ViSession instrumentHandle,
                                                       ViReal64* pSegmentMinimum);

 ViStatus  TLDFM_get_tilt_count (ViSession instrumentHandle,
                                                  ViUInt32* pTiltCount);

 ViStatus  TLDFM_get_tilt_maximum (ViSession instrumentHandle,
                                                    ViReal64* pTiltMaximum);

 ViStatus  TLDFM_get_tilt_minimum (ViSession instrumentHandle,
                                                    ViReal64* pTiltMinimum);



 ViStatus  TLDFM_set_access_level (ViSession instrumentHandle,
                                                    ViChar    accessLevel,
                                                    ViChar    accessPassword[]);

 ViStatus  TLDFM_get_device_configuration (ViSession instrumentHandle,
                                                            ViUInt32* pSegmentCnt,
                                                            ViReal64* pMinSegmentVoltage,
                                                            ViReal64* pMaxSegmentVoltage,
                                                            ViReal64* pSegmentCommonVoltageMax,
                                                            ViUInt32* pTiltElementCnt,
                                                            ViReal64* pMinTiltVoltage,
                                                            ViReal64* pMaxTiltVoltage,
                                                            ViReal64* pTiltCommonVoltageMax);

 ViStatus  TLDFM_set_device_configuration (ViSession instrumentHandle,
                                                            ViUInt32  segmentCnt,
                                                            ViReal64  minSegmentVoltage,
                                                            ViReal64  maxSegmentVoltage,
                                                            ViReal64  segmentCommonVoltageMax,
                                                            ViUInt32  tiltElementCnt,
                                                            ViReal64  minTiltVoltage,
                                                            ViReal64  maxTiltVoltage,
                                                            ViReal64  tiltCommonVoltageMax);

 ViStatus  TLDFM_get_device_calibration (ViSession instrumentHandle,
                                                          ViReal64* pSegmentVoltageCompensation,
                                                          ViReal64* pTiltVoltageCompensation,
                                                          ViReal64* pSingleSegmentTiltVoltage);

 ViStatus  TLDFM_set_device_calibration (ViSession instrumentHandle,
                                                          ViReal64  segmentVoltageCompensation,
                                                          ViReal64  tiltVoltageCompensation,
                                                          ViReal64  singleSegmentTiltVoltage);

 ViStatus  TLDFM_get_hysteresis_parameters (ViSession instrumentHandle,
                                                             ViUInt32  target,
                                                             ViUInt32* pCount,
                                                             ViReal64* pNonlinearFactor,
                                                             ViReal64  arrayTresholdInverter[],
                                                             ViReal64  arrayWeightInverter[]);

 ViStatus  TLDFM_set_hysteresis_parameters (ViSession instrumentHandle,
                                                             ViUInt32  target,
                                                             ViUInt32  count,
                                                             ViReal64  nonlinearFactor,
                                                             ViReal64  arrayTresholdInverter[],
                                                             ViReal64  arrayWeightInverter[]);

 ViStatus  TLDFM_enabled_hysteresis_compensation (ViSession  instrumentHandle,
                                                                   ViUInt32   target,
                                                                   ViBoolean* pEnabled);

 ViStatus  TLDFM_enable_hysteresis_compensation (ViSession instrumentHandle,
                                                                  ViUInt32  target,
                                                                  ViBoolean enable);



 ViStatus  TLDFM_get_measured_segment_voltage (ViSession instrumentHandle,
                                                                ViUInt32  segmentIndex,
                                                                ViReal64* pSegmentVoltage);

 ViStatus  TLDFM_get_measured_segment_voltages (ViSession instrumentHandle,
                                                                 ViReal64  segmentVoltages[]);

 ViStatus  TLDFM_get_measured_tilt_voltage (ViSession instrumentHandle,
                                                             ViUInt32  tiltIndex,
                                                             ViReal64* pTiltVoltage);

 ViStatus  TLDFM_get_measured_tilt_voltages (ViSession instrumentHandle,
                                                              ViReal64  tiltVoltages[]);

 ViStatus  TLDFM_get_measured_voltages (ViSession instrumentHandle,
                                                         ViReal64  segmentVoltages[],
                                                         ViReal64  tiltVoltages[]);

 ViStatus  TLDFM_get_feedback_voltage (ViSession instrumentHandle,
                                                        ViReal64* pFeedbackVoltage);

 ViStatus  TLDFM_get_feedback_current (ViSession instrumentHandle,
                                                        ViReal64* pFeedbackCurrent);

 ViStatus  TLDFM_get_feedback (ViSession instrumentHandle,
                                                ViReal64* pFeedbackVoltage,
                                                ViReal64* pFeedbackCurrent);

 ViStatus  TLDFM_get_monitor_voltage (ViSession instrumentHandle,
                                                       ViReal64* pMonitorVoltage);

 ViStatus  TLDFM_get_temperatures (ViSession instrumentHandle,
                                                    ViReal64* pIC1Temperatur,
                                                    ViReal64* pIC2Temperatur,
                                                    ViReal64* pMirrorTemperatur,
                                                    ViReal64* pElectronicTemperatur);