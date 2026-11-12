"""Synthetic maintenance manual for Pump P-101.

SYNTHETIC DEMONSTRATION CONTENT. This manual describes fictional equipment
at the Chennai Manufacturing Demo Site and must not be used for real maintenance.

Document metadata
- External ID: DOC-P101-MANUAL
- Title: Cooling Water Pump P-101 Maintenance Manual
- Document type: maintenance_manual
- Revision: Demo-A
- Effective date: 2025-01-15
- Equipment: PUMP-P101

## SEC-SAFETY-001 — Safety precautions

Isolate and lock out the pump and motor before removing guards or touching the coupling.
Do not bypass interlocks, and do not defeat lubrication or temperature protection.
Confirm zero energy and a closed discharge valve before opening the bearing housing.
This demonstration text does not replace site safety procedures.
An investigation produced by software is decision support and does not authorize work.

## SEC-VIBRATION-001 — Vibration guidance

Preferred drive-end vibration for this demonstration pump is about 2.0 to 3.5 mm/s.
Investigate when drive-end vibration remains above 4.5 mm/s.
Treat sustained drive-end vibration above 7.1 mm/s as a critical operating condition
and follow the site shutdown process if the level remains above that limit.
Compare the drive end with the non-drive end. A drive-end rise with a quieter
non-drive end points the inspection toward the drive-end bearing or the coupling.
Check mounting bolts and coupling alignment before returning the pump to service.

## SEC-TEMPERATURE-001 — Bearing-temperature guidance

Normal bearing temperature in this demo is about 50 to 68 °C.
A sustained drive-end bearing temperature above 75 °C requires inspection.
A sustained temperature above 82 °C is a critical limit in this demonstration.
Rising temperature together with rising vibration is consistent with lubrication
deterioration or increasing bearing friction. Confirm the sensor before concluding
that the machine is damaged.

## SEC-FLOW-001 — Low-flow troubleshooting

Expected flow is about 90 to 110 m³/h with the discharge valve near 70 to 90 percent open.
Flow remaining below 88 m³/h should be investigated. Flow remaining below 82 m³/h
is a critical demonstration limit.
Verify valve position, suction restrictions, discharge restrictions, and cavitation indicators.
Do not attribute low flow to the valve when valve position is still inside the normal band
and suction pressure is stable.

## SEC-ALIGNMENT-001 — Alignment inspection

Excess vibration can come from coupling misalignment as well as from a bearing.
Check angular and offset alignment with the approved method, and inspect the coupling
element for wear. Historical misalignment on this pump was corrected by laser alignment.
Alignment work requires the equipment to be stopped and isolated.

## SEC-BEARING-001 — Bearing inspection

Inspect the drive-end and non-drive-end bearings when vibration and temperature rise together.
Check lubricant condition, replenishment history, mounting, and unusual noise after shutdown.
Bearing replacement on this demo pump is a planned maintenance activity, not an automatic action.
A previous demonstration work order replaced the drive-end bearing after lubrication degradation.
Increasing motor current can accompany bearing friction, so compare current with the
bearing signals before focusing on the motor alone.

## SEC-SHUTDOWN-001 — Recommended shutdown conditions

Follow site procedures for a controlled shutdown when a critical vibration or bearing-temperature
limit remains exceeded. Do not keep the pump in service only because an application recommended
further checks. Software must not stop the equipment.

## SEC-PROCEDURE-001 — Maintenance procedure

1. Review the trend and the active incident.
2. Confirm sensor health and recent maintenance history.
3. Hold a pre-job safety review and isolate the equipment if intrusive inspection is required.
4. Inspect lubrication, bearings, coupling alignment, and valve condition as indicated by the evidence.
5. Record measurements, the decision, and the person who approved the work.

## SEC-REVISION-001 — Revision history

- Demo-A, 2025-01-15: Initial synthetic manual for the maintenance-investigation proof of concept.
