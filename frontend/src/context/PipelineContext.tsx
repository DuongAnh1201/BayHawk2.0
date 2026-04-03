import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type {
  AlertEvent,
  CameraNode,
  PipelineResult,
} from '../types/pipeline'
import { analyzePipeline } from '../services/api'
import { fetchNearbyWebcams, hasWindyKey, type WindyWebcam } from '../services/cameras'
import { fetchLiveWeather } from '../services/weather'

const CAMERAS: CameraNode[] = [
  { id: '1', name: 'Sierra Peak North', code: 'cam-01', lat: 34.32, lon: -117.73, online: true, alertcaId: 'Axis-MtnHighWest2' },
  { id: '2', name: 'Cajon Pass West', code: 'cam-02', lat: 34.31, lon: -117.45, online: true, alertcaId: 'Axis-LyonsPeak1' },
  { id: '3', name: 'Malibu Canyon', code: 'cam-03', lat: 34.05, lon: -118.68, online: true, alertcaId: 'Axis-Saddle2' },
  { id: '4', name: 'Angeles Crest', code: 'cam-04', lat: 34.25, lon: -118.15, online: true, alertcaId: 'Axis-SierraMadreCanyon2' },
]

export interface PayloadStock {
  type: string
  total: number
  available: number
}

export interface DroneStation {
  id: string
  name: string
  code: string
  lat: number
  lon: number
  drones: number
  dronesTotal: number
  payloads: string[]
  stock: PayloadStock[]
  status: 'ready' | 'deployed'
}

const DRONE_STATIONS: DroneStation[] = [
  {
    id: 'ds-1', name: 'Cajon Ridge Hub', code: 'DS-01', lat: 34.315, lon: -117.59,
    drones: 4, dronesTotal: 4, payloads: ['Water Bomb', 'Smoke Bomb'], status: 'ready',
    stock: [{ type: 'Water Bomb', total: 12, available: 12 }, { type: 'Smoke Bomb', total: 8, available: 8 }],
  },
  {
    id: 'ds-2', name: 'Santa Monica Station', code: 'DS-02', lat: 34.15, lon: -118.415,
    drones: 3, dronesTotal: 3, payloads: ['Water Bomb', 'Smoke Bomb', 'Retardant'], status: 'ready',
    stock: [{ type: 'Water Bomb', total: 10, available: 10 }, { type: 'Smoke Bomb', total: 6, available: 6 }, { type: 'Retardant', total: 4, available: 4 }],
  },
  {
    id: 'ds-3', name: 'San Gabriel Center', code: 'DS-03', lat: 34.23, lon: -118.00,
    drones: 5, dronesTotal: 5, payloads: ['Water Bomb', 'Smoke Bomb'], status: 'ready',
    stock: [{ type: 'Water Bomb', total: 15, available: 15 }, { type: 'Smoke Bomb', total: 10, available: 10 }],
  },
]

export type DemoScenario = 'clear' | 'smoke' | 'fire_high' | 'critical'

export const DEMO_LABELS: Record<DemoScenario, string> = {
  clear: 'All Clear',
  smoke: 'Simulate Smoke',
  fire_high: 'Simulate Fire',
  critical: 'Critical Emergency',
}

const DEMOS: Record<DemoScenario, PipelineResult> = {
  clear: {
    event_id: 'demo-clear',
    camera: { confidence: 0.03, detected: false, latency_ms: 210 },
    satellite: { thermal_confidence: 0.02, hotspot_detected: false, raw: { hotspots: [] }, latency_ms: 980 },
    weather: { wind_speed: 4.2, wind_direction: 180, humidity: 62, spread_risk: 0.146, latency_ms: 145 },
    fusion: { status: 'DISMISSED', combined_score: 0.024, reason: 'Combined score 0.02 below threshold 0.40. No evidence of fire.' },
    reasoning: {
      scene_description: 'Clear skies over mountainous terrain with healthy green vegetation. No visible smoke, haze, or thermal anomalies detected across the full 360-degree sweep.',
      key_observations: [
        'Vegetation appears healthy with normal color and moisture levels',
        'No visible smoke, haze, or particulate matter in the atmosphere',
        'Wind conditions are calm with no dust or debris movement',
        'All nearby structures appear intact with no signs of fire damage',
      ],
    },
    classification: { criticality: 'LOW', score: 0.03, reasoning: 'No fire indicators present. All sensors report nominal conditions.' },
    suggestion: {
      action_plan: ['Continue routine monitoring at standard intervals', 'No action required at this time'],
      alert_message: 'ALL CLEAR — Routine scan complete. No fire activity detected. Conditions nominal.',
      recommended_resources: [],
    },
    output: { notification_sent: false, dashboard_updated: true, incident_id: 'demo-clear-001', logged: true },
  },

  smoke: {
    event_id: 'demo-smoke',
    camera: { confidence: 0.42, detected: true, latency_ms: 315 },
    satellite: { thermal_confidence: 0.18, hotspot_detected: false, raw: { hotspots: [] }, latency_ms: 1100 },
    weather: { wind_speed: 8.3, wind_direction: 270, humidity: 35, spread_risk: 0.41, latency_ms: 162 },
    fusion: { status: 'DISMISSED', combined_score: 0.348, reason: 'Combined score 0.35 below threshold 0.40. Camera detected smoke but no thermal confirmation.' },
    reasoning: {
      scene_description: 'Light haze visible on the eastern ridge, possibly smoke from a distant source or controlled burn. No active flame front visible. Visibility reduced to approximately 3 km in the affected direction.',
      key_observations: [
        'Light haze or smoke visible along the eastern ridge line',
        'No active flames or glowing embers detected',
        'Satellite thermal scan shows no hotspot — could be residual or distant smoke',
        'Wind carrying particulate from west at 8.3 m/s',
        'Humidity at 35% — moderate fire weather conditions',
      ],
    },
    classification: { criticality: 'MEDIUM', score: 0.38, reasoning: 'Smoke detected by camera but unconfirmed by thermal satellite. Warrants close monitoring but does not yet meet confirmed fire threshold.' },
    suggestion: {
      action_plan: [
        'Increase camera monitoring frequency to 30-second intervals',
        'Dispatch ground scout to verify smoke source within 30 minutes',
        'Alert nearest fire station for potential rapid deployment',
        'Check with CAL FIRE for any permitted controlled burns in the area',
      ],
      alert_message: 'SMOKE ADVISORY — Unconfirmed smoke detected on the eastern ridge near cam-02. Ground verification in progress. No evacuation needed at this time.',
      recommended_resources: ['1× ground scout vehicle', '1× Type-3 engine on standby'],
    },
    output: { notification_sent: false, dashboard_updated: true, incident_id: 'demo-smoke-001', logged: true },
  },

  fire_high: {
    event_id: 'demo-fire-high',
    camera: { confidence: 0.87, detected: true, latency_ms: 342 },
    satellite: {
      thermal_confidence: 0.76, hotspot_detected: true,
      raw: { hotspots: [{ frp: 76.0, latitude: 34.32, longitude: -117.73 }] },
      latency_ms: 1240,
    },
    weather: { wind_speed: 13.5, wind_direction: 225, humidity: 18, spread_risk: 0.732, latency_ms: 189 },
    fusion: { status: 'CONFIRMED', combined_score: 0.826, reason: 'Combined score 0.83 meets threshold 0.40. Camera detected=true, thermal hotspot=true.' },
    reasoning: {
      scene_description: 'Dense smoke column rising from a steep hillside with active flame front advancing northeast. Chaparral and dry brush are primary fuel sources.',
      key_observations: [
        'Active flame front moving northeast driven by Santa Ana winds',
        'Dense smoke obscuring visibility beyond 500 m',
        'Dry chaparral acting as primary fuel — high burn rate expected',
        'No visible fire breaks or natural barriers ahead of the fire front',
        'Nearest structures approximately 1.2 km from current perimeter',
      ],
    },
    classification: { criticality: 'HIGH', score: 0.82, reasoning: 'Active spread with strong winds and critically low humidity warrants HIGH classification.' },
    suggestion: {
      action_plan: [
        'Deploy drone from DS-01 (Cajon Ridge Hub) with Water Bomb for immediate suppression',
        'Deploy two aerial tankers to the northern flank immediately',
        'Establish firebreak along Ridge Road before flame front arrives',
        'Evacuate residents within 2 km radius — use Route 18 eastbound',
        'Pre-position engine crews at the Pinecrest subdivision entrance',
        'Request mutual aid from neighboring county strike teams',
      ],
      alert_message: 'WILDFIRE ALERT — HIGH criticality fire detected near 34.05°N 118.25°W. Strong southwest winds driving rapid spread. Evacuation order issued for Zone A.',
      recommended_resources: ['🛸 Deploy drone from DS-01 (Cajon Ridge) — Water Bomb for immediate suppression', '2× aerial tankers (CL-415)', '4× Type-1 engine crews', '1× bulldozer for firebreak', 'Red Cross shelter at Mountain High School'],
    },
    output: { notification_sent: false, dashboard_updated: false, incident_id: 'demo-fire-001', logged: true },
  },

  critical: {
    event_id: 'demo-critical',
    camera: { confidence: 0.97, detected: true, latency_ms: 285 },
    satellite: {
      thermal_confidence: 0.94, hotspot_detected: true,
      raw: { hotspots: [
        { frp: 142.0, latitude: 34.32, longitude: -117.73 },
        { frp: 98.0, latitude: 34.33, longitude: -117.71 },
        { frp: 67.0, latitude: 34.31, longitude: -117.75 },
      ]},
      latency_ms: 890,
    },
    weather: { wind_speed: 22.4, wind_direction: 45, humidity: 8, spread_risk: 0.948, latency_ms: 130 },
    fusion: { status: 'CONFIRMED', combined_score: 0.958, reason: 'Combined score 0.96 far exceeds threshold 0.40. Camera 97% confident, 3 thermal hotspots detected. Extreme fire weather.' },
    reasoning: {
      scene_description: 'Massive fire front spanning 2+ km with multiple spot fires ahead of the main blaze. Extreme ember cast driven by 22 m/s Santa Ana winds. Structures are directly threatened. Multiple ignition points suggest crown fire behavior.',
      key_observations: [
        'Multi-kilometer fire front with active crown fire behavior',
        'Extreme ember cast creating spot fires 500+ m ahead of the front',
        'Three distinct thermal hotspots confirmed by satellite (142, 98, 67 MW)',
        'Santa Ana winds at 22.4 m/s with 8% humidity — worst-case fire weather',
        'Residential structures within 400 m of leading edge',
        'Road access compromised on the northern evacuation route',
      ],
    },
    classification: { criticality: 'CRITICAL', score: 0.96, reasoning: 'Extreme fire behavior with imminent threat to life and structures. Santa Ana wind event with single-digit humidity. Multiple thermal hotspots confirm rapid uncontrolled spread.' },
    suggestion: {
      action_plan: [
        'Deploy ALL drones from DS-01 & DS-03 with Water/Smoke Bombs for rapid containment',
        'Issue IMMEDIATE mandatory evacuation for all zones within 5 km',
        'Deploy all available aerial assets — request state and federal mutual aid',
        'Activate emergency operations center (EOC) at full capacity',
        'Close Highway 138 and Route 18 — redirect to Interstate 15 southbound',
        'Deploy structural protection crews to Pinecrest and Cedar Glen subdivisions',
        'Request National Guard assistance for evacuation support',
        'Establish unified command with USFS, CAL FIRE, and local agencies',
      ],
      alert_message: 'CRITICAL WILDFIRE EMERGENCY — Extreme fire behavior with imminent threat to life. MANDATORY EVACUATION for all areas within 5 km. Multiple structures threatened. Seek shelter immediately if unable to evacuate. Dial 911.',
      recommended_resources: [
        '🛸 Deploy ALL drones from DS-01 (Cajon Ridge) — Water & Smoke Bombs',
        '🛸 Deploy drones from DS-03 (San Gabriel) — Water Bombs for eastern flank',
        '6× aerial tankers + 2× heavy helicopters',
        '12× Type-1 engine crews',
        '3× bulldozers for firebreak construction',
        '2× hand crews (20-person)',
        'National Guard evacuation support',
        'Red Cross mass shelter activation (3 locations)',
      ],
    },
    output: { notification_sent: true, dashboard_updated: true, incident_id: 'demo-critical-001', logged: true },
  },
}

export interface DroneDispatch {
  stationId: string
  payload: string
  status: 'launching' | 'en-route' | 'dropping' | 'returning' | 'complete'
  eta: number
  startedAt: number
}

export type DeescalationPhase = 'responding' | 'containment' | 'controlled' | 'extinguished'

export const DEESCALATION_LABELS: Record<DeescalationPhase, { label: string; color: string; description: string }> = {
  responding: { label: 'Responding', color: 'text-red-400', description: 'Drones deployed, ground crews en route' },
  containment: { label: 'Containment', color: 'text-amber-400', description: 'Fire perimeter established, active suppression' },
  controlled: { label: 'Controlled', color: 'text-blue-400', description: 'Fire contained, mop-up operations underway' },
  extinguished: { label: 'Extinguished', color: 'text-emerald-400', description: 'Fire fully extinguished, scene secured' },
}

const DEESC_FIRE_HIGH: Record<DeescalationPhase, Partial<PipelineResult>> = {
  responding: {
    camera: { confidence: 0.72, detected: true, latency_ms: 310 },
    satellite: { thermal_confidence: 0.58, hotspot_detected: true, raw: { hotspots: [{ frp: 52.0, latitude: 34.32, longitude: -117.73 }] }, latency_ms: 1100 },
    fusion: { status: 'CONFIRMED', combined_score: 0.68, reason: 'Drone water bomb impacting target area. Thermal signature reducing.' },
    classification: { criticality: 'HIGH', score: 0.68, reasoning: 'Active suppression underway. Drone payload deployed on hotspot. Ground crews establishing firebreak on Ridge Road.' },
    reasoning: {
      scene_description: 'Drone water bomb has impacted the primary hotspot. Steam plume visible as water contacts active burn area. Ground crews visible on Ridge Road establishing firebreak.',
      key_observations: [
        'Drone payload (Water Bomb) successfully delivered to primary hotspot',
        'Steam plume visible — active cooling of burn area',
        'Ground crews establishing firebreak along Ridge Road',
        'Flame front advance slowing due to suppression efforts',
        'Wind still elevated at 12 m/s but fire spread rate decreasing',
      ],
    },
    suggestion: {
      action_plan: ['Drone payload delivered — monitoring cooling effect', 'Ground crews establishing firebreak on Ridge Road', 'Second drone on standby for follow-up drop', 'Continue evacuee coordination on Route 18'],
      alert_message: 'UPDATE — Suppression underway. Drone water bomb delivered to primary hotspot. Ground crews on scene establishing containment lines.',
      recommended_resources: ['🛸 DS-01 drone payload delivered — monitoring', '2× engine crews on firebreak', '1× aerial tanker inbound ETA 8 min'],
    },
  },
  containment: {
    camera: { confidence: 0.45, detected: true, latency_ms: 295 },
    satellite: { thermal_confidence: 0.31, hotspot_detected: true, raw: { hotspots: [{ frp: 18.0, latitude: 34.32, longitude: -117.73 }] }, latency_ms: 950 },
    fusion: { status: 'CONFIRMED', combined_score: 0.41, reason: 'Fire perimeter established. Thermal signature significantly reduced.' },
    classification: { criticality: 'MEDIUM', score: 0.45, reasoning: 'Fire 70% contained. Firebreak holding on all flanks. Drone and aerial tanker suppression effective.' },
    reasoning: {
      scene_description: 'Fire perimeter established with firebreak holding on all flanks. Smoke turning white indicating reduced combustion. Residual hotspot cooling under continued suppression.',
      key_observations: [
        'Firebreak holding — no fire crossing Ridge Road',
        'Smoke color shifting from black to white (cooling)',
        'FRP dropped from 76 MW to 18 MW — 76% reduction',
        'Second drone drop completed on residual hotspot',
        'Aerial tanker retardant line visible on northern flank',
        'No structures damaged — evacuation zone holding',
      ],
    },
    suggestion: {
      action_plan: ['Maintain containment lines — firebreak holding', 'Mop-up crews beginning interior work', 'Reduce evacuation zone to 500 m radius', 'Continue aerial monitoring for spot fires'],
      alert_message: 'CONTAINMENT — Fire 70% contained. Firebreak holding. FRP reduced 76%. No structures damaged. Evacuation zone being reduced.',
      recommended_resources: ['2× mop-up hand crews', '1× drone for thermal monitoring', 'Partial stand-down of aerial assets'],
    },
  },
  controlled: {
    camera: { confidence: 0.15, detected: false, latency_ms: 280 },
    satellite: { thermal_confidence: 0.08, hotspot_detected: false, raw: { hotspots: [] }, latency_ms: 900 },
    fusion: { status: 'DISMISSED', combined_score: 0.12, reason: 'No active fire detected. Residual heat only.' },
    classification: { criticality: 'LOW', score: 0.15, reasoning: 'Fire controlled. No active flames. Residual heat being monitored. Safe for mop-up operations.' },
    reasoning: {
      scene_description: 'No active flames visible. Light residual smoke from cooling embers. Ground crews conducting interior mop-up. Drone thermal scan confirms no re-ignition risk.',
      key_observations: [
        'No active flames detected by camera or satellite',
        'Residual smoke dissipating — visibility improving',
        'Drone thermal scan: all hotspots below re-ignition threshold',
        'Ground crews successfully extinguishing remaining embers',
        'Firebreak intact — no spot fires detected beyond perimeter',
        'All structures intact — zero property damage',
      ],
    },
    suggestion: {
      action_plan: ['Continue mop-up operations for 2 hours', 'Drone station returning to ready status', 'Lift evacuation order — residents may return', 'File incident report and debrief teams'],
      alert_message: 'CONTROLLED — Fire fully controlled. No active flames. Mop-up in progress. Evacuation order lifted. Residents may return.',
      recommended_resources: ['1× mop-up hand crew', 'Drone returning to station — mission complete'],
    },
  },
  extinguished: {
    camera: { confidence: 0.02, detected: false, latency_ms: 210 },
    satellite: { thermal_confidence: 0.01, hotspot_detected: false, raw: { hotspots: [] }, latency_ms: 850 },
    weather: { wind_speed: 5.1, wind_direction: 180, humidity: 48, spread_risk: 0.08, latency_ms: 140 },
    fusion: { status: 'DISMISSED', combined_score: 0.015, reason: 'Scene clear. No thermal anomalies. Fire fully extinguished.' },
    classification: { criticality: 'LOW', score: 0.02, reasoning: 'Fire extinguished. All clear. Scene secured by ground teams. Drone operations completed successfully.' },
    reasoning: {
      scene_description: 'Fire completely extinguished. Scene secured. Burned area visible but no smoke, heat, or active combustion detected. All personnel safe. Successful joint drone and ground crew operation.',
      key_observations: [
        'Fire 100% extinguished — confirmed by aerial and ground assessment',
        'Total burned area: approximately 2.3 acres (contained by rapid drone response)',
        'Zero structures damaged, zero injuries reported',
        'Drone response time: 90 seconds from alert to first payload drop',
        'Ground crew response: 8 minutes from dispatch to on-scene',
        'Combined drone + ground operation contained fire in under 25 minutes',
      ],
    },
    suggestion: {
      action_plan: ['Incident secured — all units stand down', 'File final incident report (IR-2026-0401)', 'Debrief all teams within 24 hours', 'Replenish drone payloads at DS-01', 'Schedule post-fire vegetation assessment'],
      alert_message: 'ALL CLEAR — Fire extinguished. 2.3 acres burned. Zero damage, zero injuries. Rapid drone response contained spread. All units standing down.',
      recommended_resources: [],
    },
    output: { notification_sent: true, dashboard_updated: true, incident_id: 'demo-fire-001', logged: true },
  },
}

const DEESC_CRITICAL: Record<DeescalationPhase, Partial<PipelineResult>> = {
  responding: {
    camera: { confidence: 0.88, detected: true, latency_ms: 290 },
    satellite: { thermal_confidence: 0.78, hotspot_detected: true, raw: { hotspots: [{ frp: 110.0, latitude: 34.32, longitude: -117.73 }, { frp: 72.0, latitude: 34.33, longitude: -117.71 }] }, latency_ms: 880 },
    fusion: { status: 'CONFIRMED', combined_score: 0.84, reason: 'Multi-drone suppression underway. Thermal signatures reducing but still elevated.' },
    classification: { criticality: 'CRITICAL', score: 0.84, reasoning: 'Multiple drones deployed. Ground crews and aerial tankers engaged. Fire still active but suppression efforts reducing spread rate significantly.' },
    reasoning: {
      scene_description: 'Multiple drones delivering water and smoke bombs across the fire front. Aerial tankers dropping retardant on the northern flank. Ground crews cutting firebreaks on two sides.',
      key_observations: [
        'DS-01 drones delivering Water Bombs to primary hotspot cluster',
        'DS-03 drones deploying Smoke Bombs on eastern flank to slow advance',
        'Aerial tanker retardant line established on northern perimeter',
        'Ground crews cutting emergency firebreak on southern exposure',
        'Ember cast reduced — drone smoke suppression limiting spot fires',
        'Evacuation 80% complete — National Guard assisting',
      ],
    },
    suggestion: {
      action_plan: ['Multi-drone strike in progress — 6 drones active', 'Aerial tanker retardant drop on northern flank complete', 'Ground crews advancing firebreak on south side', 'Evacuation continuing — Route 18 clear', 'Second wave of drone payloads being loaded'],
      alert_message: 'RESPONSE UPDATE — Massive multi-asset response underway. 6 drones, 2 aerial tankers, 12 engine crews engaged. Fire spread rate decreasing.',
      recommended_resources: ['🛸 6 drones active (DS-01 + DS-03)', '2× aerial tankers dropping retardant', '12× engine crews on containment lines'],
    },
  },
  containment: {
    camera: { confidence: 0.52, detected: true, latency_ms: 275 },
    satellite: { thermal_confidence: 0.38, hotspot_detected: true, raw: { hotspots: [{ frp: 35.0, latitude: 34.32, longitude: -117.73 }] }, latency_ms: 860 },
    fusion: { status: 'CONFIRMED', combined_score: 0.47, reason: 'Fire perimeter established on 3 of 4 flanks. Main hotspot cooling rapidly.' },
    classification: { criticality: 'HIGH', score: 0.52, reasoning: 'Downgraded from CRITICAL. Fire perimeter 80% established. Drone suppression reduced FRP by 75%. One remaining active flank under assault.' },
    reasoning: {
      scene_description: 'Fire perimeter established on three flanks. Remaining eastern flank being suppressed by coordinated drone and aerial tanker operations. Smoke density decreasing across the scene.',
      key_observations: [
        'Fire downgraded from CRITICAL to HIGH — containment progress',
        'Three of four flanks contained with firebreaks',
        'FRP reduced from peak 142 MW to 35 MW — 75% reduction',
        'Hotspot count reduced from 3 to 1 active',
        'Drone smoke suppression eliminated 90% of ember cast',
        'All residential areas secured — zero structures lost',
        'Eastern flank being closed by aerial tanker support',
      ],
    },
    suggestion: {
      action_plan: ['Close eastern flank with final aerial tanker pass', 'Drone thermal scanning for hidden hotspots', 'Begin reducing evacuation zone perimeter', 'Pre-position mop-up crews for interior work', 'Maintain unified command until full containment'],
      alert_message: 'CONTAINMENT PROGRESS — Fire downgraded to HIGH. 3 of 4 flanks contained. FRP reduced 75%. Zero structures lost. Eastern flank closing.',
      recommended_resources: ['🛸 3 drones on thermal patrol', '1× aerial tanker for final eastern pass', '4× mop-up hand crews staging'],
    },
  },
  controlled: {
    camera: { confidence: 0.18, detected: false, latency_ms: 260 },
    satellite: { thermal_confidence: 0.06, hotspot_detected: false, raw: { hotspots: [] }, latency_ms: 830 },
    fusion: { status: 'DISMISSED', combined_score: 0.11, reason: 'All flanks contained. No active fire detected. Residual heat in controlled area.' },
    classification: { criticality: 'LOW', score: 0.18, reasoning: 'Fire 100% contained. All four flanks secured. Mop-up operations proceeding. Drones returning to stations.' },
    reasoning: {
      scene_description: 'All four flanks fully contained. No active flames visible. Extensive retardant and water coverage visible across the burn scar. Ground crews conducting systematic mop-up.',
      key_observations: [
        'All 4 flanks contained — fire perimeter fully secured',
        'No active flames — satellite confirms zero hotspots above threshold',
        'All drones returning to stations for payload replenishment',
        'Mop-up crews working interior for hidden embers',
        'Zero structures damaged across the entire incident',
        'Zero civilian or firefighter injuries reported',
        'Evacuation order being lifted zone by zone',
      ],
    },
    suggestion: {
      action_plan: ['Full containment achieved — begin demobilization', 'Drones returning to stations for refit', 'Lift evacuation in phases — Zone C first', 'Continue mop-up for 4 hours minimum', 'Initiate incident after-action review'],
      alert_message: 'CONTROLLED — Fire 100% contained. All flanks secured. Zero damage, zero injuries. Evacuation orders being lifted. Demobilization underway.',
      recommended_resources: ['2× mop-up crews (4-hour rotation)', 'Drone stations restocking payloads'],
    },
  },
  extinguished: {
    camera: { confidence: 0.01, detected: false, latency_ms: 200 },
    satellite: { thermal_confidence: 0.005, hotspot_detected: false, raw: { hotspots: [] }, latency_ms: 800 },
    weather: { wind_speed: 4.8, wind_direction: 200, humidity: 52, spread_risk: 0.06, latency_ms: 130 },
    fusion: { status: 'DISMISSED', combined_score: 0.008, reason: 'Scene fully cleared. No thermal anomalies detected in 360-degree scan.' },
    classification: { criticality: 'LOW', score: 0.01, reasoning: 'Incident closed. Fire completely extinguished. All assets demobilized. Exemplary multi-agency, drone-assisted response.' },
    reasoning: {
      scene_description: 'Fire completely extinguished and scene secured. Burn scar visible across approximately 12 acres — significantly less than projected 200+ acres without drone intervention. All personnel safe.',
      key_observations: [
        'Fire 100% extinguished — confirmed by ground, aerial, and satellite assessment',
        'Total burned area: 12 acres (projected 200+ acres without rapid drone response)',
        'Drone intervention saved an estimated 190+ acres of wildland',
        'Zero structures damaged (156 structures were in the projected fire path)',
        'Zero injuries — all civilians evacuated safely',
        'Total response time from detection to extinguishment: 47 minutes',
        'Drone response: 90 sec to first payload, 9 drones deployed across 2 stations',
        'This incident demonstrates the critical value of drone-assisted rapid response',
      ],
    },
    suggestion: {
      action_plan: ['Incident CLOSED — all units standing down', 'Final incident report filed (IR-2026-0401-CRITICAL)', 'Commendation recommended for drone operations team', 'All drone stations resupplied and operational', 'Post-incident vegetation and watershed assessment scheduled', 'Media briefing: successful drone-assisted fire suppression'],
      alert_message: 'ALL CLEAR — Critical wildfire extinguished. 12 acres burned (saved 190+ acres via drone response). Zero damage. Zero injuries. Total response: 47 minutes. All units standing down.',
      recommended_resources: [],
    },
    output: { notification_sent: true, dashboard_updated: true, incident_id: 'demo-critical-001', logged: true },
  },
}

function getNearestStation(lat: number, lon: number, stations: DroneStation[]): DroneStation | null {
  let best: DroneStation | null = null
  let bestDist = Infinity
  for (const s of stations) {
    const d = Math.sqrt((s.lat - lat) ** 2 + (s.lon - lon) ** 2)
    if (d < bestDist && s.status === 'ready') {
      bestDist = d
      best = s
    }
  }
  return best
}

interface PipelineContextValue {
  cameras: CameraNode[]
  selectedCamera: string
  setSelectedCamera: (id: string) => void
  pipelineResult: PipelineResult | null
  activeScenario: DemoScenario | null
  isAnalyzing: boolean
  error: string | null
  runAnalysis: () => Promise<void>
  loadDemo: (scenario: DemoScenario) => Promise<void>
  liveFeed: WindyWebcam | null
  liveFeedLoading: boolean
  hasLiveFeedKey: boolean
  droneStations: DroneStation[]
  droneDispatches: DroneDispatch[]
  nearestStation: DroneStation | null
  dispatchDrone: (stationId: string, payload: string) => void
  resetDrones: () => void
  deescalationPhase: DeescalationPhase | null
  isDeescalating: boolean
  startDeescalation: () => void
}

const PipelineContext = createContext<PipelineContextValue | undefined>(undefined)

export function PipelineProvider({ children }: { children: ReactNode }) {
  const [selectedCamera, setSelectedCamera] = useState('1')
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null)
  const [activeScenario, setActiveScenario] = useState<DemoScenario | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [liveFeed, setLiveFeed] = useState<WindyWebcam | null>(null)
  const [liveFeedLoading, setLiveFeedLoading] = useState(false)
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const [stations, setStations] = useState<DroneStation[]>(() => DRONE_STATIONS.map(s => ({ ...s, stock: s.stock.map(st => ({ ...st })) })))
  const [droneDispatches, setDroneDispatches] = useState<DroneDispatch[]>([])

  const nearestStation = useMemo(() => {
    const cam = CAMERAS.find(c => c.id === selectedCamera)
    if (!cam) return null
    return getNearestStation(cam.lat, cam.lon, stations)
  }, [selectedCamera, stations])

  const dispatchDrone = useCallback((stationId: string, payload: string) => {
    setStations(prev => prev.map(s => {
      if (s.id !== stationId) return s
      return {
        ...s,
        status: 'deployed' as const,
        drones: Math.max(0, s.drones - 1),
        stock: s.stock.map(st => st.type === payload ? { ...st, available: Math.max(0, st.available - 1) } : st),
      }
    }))
    const dispatch: DroneDispatch = { stationId, payload, status: 'launching', eta: 90, startedAt: Date.now() }
    setDroneDispatches(prev => [...prev, dispatch])

    const phases: DroneDispatch['status'][] = ['en-route', 'dropping', 'returning', 'complete']
    const delays = [3000, 6000, 10000, 14000]
    phases.forEach((phase, i) => {
      setTimeout(() => {
        setDroneDispatches(prev =>
          prev.map(d => d.stationId === stationId && d.startedAt === dispatch.startedAt
            ? { ...d, status: phase, eta: Math.max(0, 90 - (delays[i]! / 1000) * 6) }
            : d,
          ),
        )
        if (phase === 'complete') {
          setTimeout(() => {
            setStations(prev => prev.map(s => s.id === stationId ? { ...s, status: 'ready' as const, drones: s.drones + 1 } : s))
          }, 4000)
        }
      }, delays[i])
    })
  }, [])

  const resetDrones = useCallback(() => {
    setStations(DRONE_STATIONS.map(s => ({ ...s, stock: s.stock.map(st => ({ ...st })) })))
    setDroneDispatches([])
  }, [])

  const [deescalationPhase, setDeescalationPhase] = useState<DeescalationPhase | null>(null)
  const [isDeescalating, setIsDeescalating] = useState(false)
  const deescTimers = useRef<ReturnType<typeof setTimeout>[]>([])

  const startDeescalation = useCallback(() => {
    if (isDeescalating) return
    const scenario = activeScenario
    if (scenario !== 'fire_high' && scenario !== 'critical') return

    const phaseData = scenario === 'critical' ? DEESC_CRITICAL : DEESC_FIRE_HIGH
    const phases: DeescalationPhase[] = ['responding', 'containment', 'controlled', 'extinguished']
    const delays = [0, 8000, 18000, 28000]

    setIsDeescalating(true)

    if (scenario === 'fire_high') {
      dispatchDrone('ds-1', 'Water Bomb')
    } else {
      dispatchDrone('ds-1', 'Water Bomb')
      dispatchDrone('ds-1', 'Smoke Bomb')
      setTimeout(() => {
        dispatchDrone('ds-3', 'Water Bomb')
        dispatchDrone('ds-3', 'Water Bomb')
      }, 1500)
    }

    deescTimers.current.forEach(clearTimeout)
    deescTimers.current = []

    phases.forEach((phase, i) => {
      const t = setTimeout(() => {
        setDeescalationPhase(phase)
        setPipelineResult(prev => {
          if (!prev) return prev
          return { ...prev, ...phaseData[phase] }
        })
        if (phase === 'extinguished') {
          setActiveScenario(null)
          setTimeout(() => {
            setIsDeescalating(false)
            resetDrones()
          }, 5000)
        }
      }, delays[i])
      deescTimers.current.push(t)
    })
  }, [isDeescalating, activeScenario, dispatchDrone, resetDrones])

  const loadLiveFeed = useCallback(async (camId: string) => {
    const cam = CAMERAS.find(c => c.id === camId)
    if (!cam || !hasWindyKey()) return

    setLiveFeedLoading(true)
    try {
      const webcams = await fetchNearbyWebcams(cam.lat, cam.lon)
      setLiveFeed(webcams[0] ?? null)
    } catch {
      setLiveFeed(null)
    } finally {
      setLiveFeedLoading(false)
    }
  }, [])

  useEffect(() => {
    loadLiveFeed(selectedCamera)

    if (refreshTimer.current) clearInterval(refreshTimer.current)
    refreshTimer.current = setInterval(() => loadLiveFeed(selectedCamera), 8 * 60 * 1000)

    return () => {
      if (refreshTimer.current) clearInterval(refreshTimer.current)
    }
  }, [selectedCamera, loadLiveFeed])

  const runAnalysis = useCallback(async () => {
    const cam = CAMERAS.find(c => c.id === selectedCamera)
    if (!cam) return

    setIsAnalyzing(true)
    setError(null)
    setActiveScenario(null)

    const event: AlertEvent = {
      event_id: `evt-${Date.now()}`,
      lat: cam.lat,
      lon: cam.lon,
      camera_id: cam.code,
      timestamp: new Date().toISOString(),
    }

    try {
      const result = await analyzePipeline(event)
      setPipelineResult(result)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Analysis failed'
      setError(msg)
    } finally {
      setIsAnalyzing(false)
    }
  }, [selectedCamera])

  const loadDemo = useCallback(async (scenario: DemoScenario) => {
    const cam = CAMERAS.find(c => c.id === selectedCamera)
    setError(null)
    setActiveScenario(scenario)
    setDeescalationPhase(null)
    setIsDeescalating(false)
    deescTimers.current.forEach(clearTimeout)
    deescTimers.current = []

    const result = { ...DEMOS[scenario] }

    if (cam) {
      const liveWeather = await fetchLiveWeather(cam.lat, cam.lon)
      if (liveWeather) {
        result.weather = liveWeather.weather
        result.camera = { ...result.camera!, latency_ms: liveWeather.latencyMs }
        result.satellite = { ...result.satellite!, latency_ms: liveWeather.latencyMs }
      }
    }

    setPipelineResult(result)
  }, [selectedCamera])

  return (
    <PipelineContext.Provider
      value={{
        cameras: CAMERAS,
        selectedCamera,
        setSelectedCamera,
        pipelineResult,
        activeScenario,
        isAnalyzing,
        error,
        runAnalysis,
        loadDemo,
        liveFeed,
        liveFeedLoading,
        hasLiveFeedKey: hasWindyKey(),
        droneStations: stations,
        droneDispatches,
        nearestStation,
        dispatchDrone,
        resetDrones,
        deescalationPhase,
        isDeescalating,
        startDeescalation,
      }}
    >
      {children}
    </PipelineContext.Provider>
  )
}

export function usePipeline() {
  const ctx = useContext(PipelineContext)
  if (!ctx) throw new Error('usePipeline must be used within PipelineProvider')
  return ctx
}
