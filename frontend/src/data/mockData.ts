import { DecisionDispatch } from '../types';

export const INITIAL_DECISIONS: DecisionDispatch[] = [
  {
    step: 9281,
    timeUTC: '14:42:08 UTC',
    action: 'HYBRID',
    status: 'APPROVED',
    riskLevel: 'Low',
    cedarReason: 'Cedar policy rule #104 satisfied: thermal boundary conditions within allowable limits.',
    strategyReason:
      'High thermal load detected across primary heat-exchange nodes; hybrid mode selected to balance airflow and pump circulation.',
    safetyFilterReason:
      'Transient delta within nominal operating envelope; no intervention required.',
    telemetryVectors: {
      temperature_deviation: '+2.8°C',
      water_usage: '4.2 gal/min',
      liquid_outlet_temp: '38.2°C',
      cooling_efficiency: '94.6%',
    },
    cedarSafetyVerdict: {
      risk_score: '0.12',
      intervention_applied: 'No',
      reason: 'Operating within certified thermodynamic bounds.',
    },
    rewardBreakdown: {
      thermal_stability: '+0.85',
      energy_penalty: '-0.18',
      water_conservation: '+0.42',
      equipment_strain: '0.00',
    },
    details: {
      liquidRatio: '65%',
      airRatio: '35%',
      powerSaved: '18.6 kWh/hr',
    },
  },
  {
    step: 9280,
    timeUTC: '14:27:00 UTC',
    action: 'LIQUID',
    status: 'APPROVED',
    riskLevel: 'Low',
    cedarReason: 'Cedar policy rule #88 satisfied: primary coolant pump flow within laminar velocity specs.',
    strategyReason:
      'Sustained high-density matrix compute cluster active; full liquid cooling engaged for rapid dissipation.',
    safetyFilterReason:
      'Return manifold temperature below 41°C ceiling; safety envelope fully respected.',
    telemetryVectors: {
      temperature_deviation: '+1.4°C',
      water_usage: '6.1 gal/min',
      liquid_outlet_temp: '35.4°C',
      cooling_efficiency: '96.2%',
    },
    cedarSafetyVerdict: {
      risk_score: '0.09',
      intervention_applied: 'No',
      reason: 'Flow rate compliant with ASTM thermal conductivity models.',
    },
    rewardBreakdown: {
      thermal_stability: '+0.92',
      energy_penalty: '-0.24',
      water_conservation: '+0.15',
      equipment_strain: '+0.02',
    },
    details: {
      liquidRatio: '100%',
      airRatio: '0%',
      powerSaved: '22.1 kWh/hr',
    },
  },
  {
    step: 9279,
    timeUTC: '14:12:12 UTC',
    action: 'AIR',
    status: 'APPROVED',
    riskLevel: 'Medium',
    cedarReason: 'Cedar policy rule #72 satisfied: external economizer air quality meets ISO-14644 standards.',
    strategyReason:
      'Ambient outdoor dry-bulb temp dropped to 14.8°C; transitioned to air-side free cooling.',
    safetyFilterReason:
      'Humidity buffer maintained above condensation dew point threshold.',
    telemetryVectors: {
      temperature_deviation: '-0.6°C',
      water_usage: '0.8 gal/min',
      liquid_outlet_temp: '32.1°C',
      cooling_efficiency: '91.8%',
    },
    cedarSafetyVerdict: {
      risk_score: '0.28',
      intervention_applied: 'No',
      reason: 'Dew point safety differential +4.2°C above condensation baseline.',
    },
    rewardBreakdown: {
      thermal_stability: '+0.64',
      energy_penalty: '+0.45',
      water_conservation: '+0.88',
      equipment_strain: '-0.05',
    },
    details: {
      liquidRatio: '10%',
      airRatio: '90%',
      powerSaved: '31.4 kWh/hr',
    },
  },
  {
    step: 9278,
    timeUTC: '13:57:04 UTC',
    action: 'HYBRID',
    status: 'APPROVED',
    riskLevel: 'Low',
    cedarReason: 'Cedar policy rule #104 satisfied: thermal boundary conditions within allowable limits.',
    strategyReason:
      'Transient accelerator burst on Row B; hybrid modulation prevents sudden cold-plate thermal shock.',
    safetyFilterReason:
      'Ramp rate constrained to maximum 0.8°C/minute as mandated by hardware warranty policy.',
    telemetryVectors: {
      temperature_deviation: '+2.1°C',
      water_usage: '3.9 gal/min',
      liquid_outlet_temp: '37.8°C',
      cooling_efficiency: '93.5%',
    },
    cedarSafetyVerdict: {
      risk_score: '0.14',
      intervention_applied: 'No',
      reason: 'Ramp-rate limits strictly verified in Cedar AST.',
    },
    rewardBreakdown: {
      thermal_stability: '+0.81',
      energy_penalty: '-0.15',
      water_conservation: '+0.48',
      equipment_strain: '0.00',
    },
    details: {
      liquidRatio: '60%',
      airRatio: '40%',
      powerSaved: '16.8 kWh/hr',
    },
  },
  {
    step: 9277,
    timeUTC: '13:42:00 UTC',
    action: 'LIQUID',
    status: 'BLOCKED',
    riskLevel: 'High',
    cedarReason: 'Cedar policy violation #118: requested valve opening 98% exceeds emergency delta-P safety invariant.',
    strategyReason:
      'RL policy suggested aggressive pump ramp to mitigate sudden 8 kW thermal spike in Pod 4.',
    safetyFilterReason:
      'Blocked by Cedar formal verifier: rapid valve stroke risks water-hammer cavitation in copper manifold.',
    telemetryVectors: {
      temperature_deviation: '+4.9°C',
      water_usage: '8.4 gal/min',
      liquid_outlet_temp: '43.1°C',
      cooling_efficiency: '82.4%',
    },
    cedarSafetyVerdict: {
      risk_score: '0.84',
      intervention_applied: 'Yes',
      reason: 'Pressure gradient spike predicted: safety interlock clamped action to safe fallback.',
    },
    rewardBreakdown: {
      thermal_stability: '-0.42',
      energy_penalty: '-0.68',
      water_conservation: '-0.30',
      equipment_strain: '-0.95',
    },
    details: {
      liquidRatio: 'Clamped',
      airRatio: 'Backup Fans 100%',
      powerSaved: '0.0 kWh/hr',
    },
  },
  {
    step: 9276,
    timeUTC: '13:27:00 UTC',
    action: 'AIR',
    status: 'APPROVED',
    riskLevel: 'Low',
    cedarReason: 'Cedar policy rule #59 satisfied: steady-state low-compute cluster profile.',
    strategyReason:
      'Overnight batch jobs concluded; facility load lowered to 320 kW baseline.',
    safetyFilterReason:
      'CRAC blower speed dialed down to 45% RPM to preserve motor bearing lifespan.',
    telemetryVectors: {
      temperature_deviation: '+0.2°C',
      water_usage: '0.5 gal/min',
      liquid_outlet_temp: '29.8°C',
      cooling_efficiency: '97.1%',
    },
    cedarSafetyVerdict: {
      risk_score: '0.05',
      intervention_applied: 'No',
      reason: 'All rack exhaust temperatures nominal and balanced.',
    },
    rewardBreakdown: {
      thermal_stability: '+0.95',
      energy_penalty: '+0.52',
      water_conservation: '+0.92',
      equipment_strain: '0.00',
    },
    details: {
      liquidRatio: '0%',
      airRatio: '100%',
      powerSaved: '38.2 kWh/hr',
    },
  },
];

export function generateNewStep(prevStep: number): DecisionDispatch {
  const nextStepNum = prevStep + 1;
  const actions: Array<'HYBRID' | 'LIQUID' | 'AIR'> = ['HYBRID', 'LIQUID', 'AIR'];
  const action = actions[Math.floor(Math.random() * actions.length)];
  const isApproved = Math.random() > 0.15;
  const status = isApproved ? 'APPROVED' : 'BLOCKED';
  const riskLevel = isApproved ? (Math.random() > 0.5 ? 'Low' : 'Medium') : 'High';

  const now = new Date();
  const timeStr = `${now.getUTCHours().toString().padStart(2, '0')}:${now.getUTCMinutes().toString().padStart(2, '0')}:${now.getUTCSeconds().toString().padStart(2, '0')} UTC`;

  const tempDev = (Math.random() * 3 - 0.5).toFixed(1);
  const tempSign = parseFloat(tempDev) >= 0 ? `+${tempDev}` : tempDev;
  const waterUsage = (Math.random() * 5 + 1.2).toFixed(1);
  const liquidTemp = (33 + Math.random() * 7).toFixed(1);
  const efficiency = (90 + Math.random() * 8).toFixed(1);

  return {
    step: nextStepNum,
    timeUTC: timeStr,
    action,
    status,
    riskLevel,
    cedarReason: isApproved
      ? `Cedar policy rule #${100 + Math.floor(Math.random() * 30)} satisfied: thermal boundary conditions within allowable limits.`
      : `Cedar policy violation #${110 + Math.floor(Math.random() * 20)}: proposed delta-P exceeded safety threshold. Action clamped.`,
    strategyReason:
      action === 'HYBRID'
        ? 'Thermal gradient across multi-tenant accelerators balanced between liquid manifold and air plenum.'
        : action === 'LIQUID'
        ? 'High GPU inference load observed on cluster-iad04; secondary coolant loop prioritized.'
        : 'Low ambient exterior conditions detected; economizer airflow activated to optimize efficiency.',
    safetyFilterReason: isApproved
      ? 'Formal verification passed in 0.32ms with zero invariant transgressions.'
      : 'Cedar hard safety boundary intercepted non-compliant valve proposal before PLC dispatch.',
    telemetryVectors: {
      temperature_deviation: `${tempSign}°C`,
      water_usage: `${waterUsage} gal/min`,
      liquid_outlet_temp: `${liquidTemp}°C`,
      cooling_efficiency: `${efficiency}%`,
    },
    cedarSafetyVerdict: {
      risk_score: (isApproved ? Math.random() * 0.25 : 0.75 + Math.random() * 0.2).toFixed(2),
      intervention_applied: isApproved ? 'No' : 'Yes',
      reason: isApproved
        ? 'Operating safely within certified thermodynamic boundaries.'
        : 'Intervention triggered: fallback to calibrated fail-safe setpoint.',
    },
    rewardBreakdown: {
      thermal_stability: (Math.random() * 0.4 + 0.6).toFixed(2),
      energy_penalty: `-${(Math.random() * 0.3 + 0.05).toFixed(2)}`,
      water_conservation: `+${(Math.random() * 0.4 + 0.2).toFixed(2)}`,
      equipment_strain: '0.00',
    },
    details: {
      liquidRatio: action === 'LIQUID' ? '100%' : action === 'HYBRID' ? '65%' : '0%',
      airRatio: action === 'AIR' ? '100%' : action === 'HYBRID' ? '35%' : '0%',
      powerSaved: `${(Math.random() * 15 + 12).toFixed(1)} kWh/hr`,
    },
  };
}
