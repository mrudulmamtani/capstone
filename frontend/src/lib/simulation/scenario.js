const ZONE_COLORS = ['#0f766e', '#2563eb', '#7c3aed', '#ea580c', '#dc2626', '#0891b2'];

const IMPACT_CONTROLS = [
  {
    id: 'throughputPressure',
    label: 'Throughput pressure',
    description: 'Pushes takt time and amplifies congestion in core processing zones.',
    min: 0,
    max: 100,
    step: 1,
    defaultValue: 58,
  },
  {
    id: 'staffingLevel',
    label: 'Staffing level',
    description: 'Low staffing extends handoffs and raises queueing around critical stations.',
    min: 0,
    max: 100,
    step: 1,
    defaultValue: 74,
  },
  {
    id: 'equipmentStrain',
    label: 'Equipment strain',
    description: 'Higher strain intensifies wear-driven slowdowns and asset hotspots.',
    min: 0,
    max: 100,
    step: 1,
    defaultValue: 46,
  },
  {
    id: 'safetySensitivity',
    label: 'Safety sensitivity',
    description: 'Higher sensitivity increases exposure scoring around violations and crossings.',
    min: 0,
    max: 100,
    step: 1,
    defaultValue: 63,
  },
  {
    id: 'qualitySensitivity',
    label: 'Quality sensitivity',
    description: 'Higher sensitivity holds more work for inspection and re-check loops.',
    min: 0,
    max: 100,
    step: 1,
    defaultValue: 57,
  },
];

const TRIGGER_LIBRARY = {
  equipmentFault: {
    id: 'equipmentFault',
    label: 'Equipment fault',
    description: 'Creates local slowdowns and repeated execution attempts around machine-heavy steps.',
  },
  congestionSpike: {
    id: 'congestionSpike',
    label: 'Congestion spike',
    description: 'Raises occupancy around handoff corridors and dispatch/service thresholds.',
  },
  qualityHold: {
    id: 'qualityHold',
    label: 'Quality hold',
    description: 'Adds review friction around QA, inspection, and release stations.',
  },
  contaminationAlert: {
    id: 'contaminationAlert',
    label: 'Contamination alert',
    description: 'Elevates hygienic/risk-sensitive zones and boosts safety + quality heat.',
  },
  forkliftSurge: {
    id: 'forkliftSurge',
    label: 'Forklift surge',
    description: 'Intensifies logistics crossings, dock activity, and pedestrian conflict points.',
  },
  rushOrder: {
    id: 'rushOrder',
    label: 'Rush order',
    description: 'Pushes the entire flow faster, increasing takt pressure and spillover heat.',
  },
};

function zone(id, label, bounds) {
  return { id, label, bounds };
}

function step(title, zoneId, asset, flowGrid, blueprintPosition, duration, heat, risk = 0.48) {
  return {
    title,
    zoneId,
    asset,
    flowGrid,
    blueprintPosition,
    duration,
    heat,
    risk,
  };
}

function createProfile(profile) {
  const zones = profile.zones.map((item, index) => ({
    ...item,
    color: ZONE_COLORS[index % ZONE_COLORS.length],
  }));

  return {
    ...profile,
    zones,
    steps: profile.steps.map((item, index) => {
      const zoneMeta = zones.find((zoneItem) => zoneItem.id === item.zoneId);
      const [column = index % 5, row = Math.floor(index / 5)] = item.flowGrid || [];
      return {
        id: `${profile.id}-step-${index + 1}`,
        order: index,
        step_index: index,
        title: item.title,
        action_label: item.title,
        zone: zoneMeta?.label || item.zoneId,
        zoneId: item.zoneId,
        asset: item.asset,
        target_duration_s: item.duration,
        tolerance_s: Math.max(0.7, Number((item.duration * 0.12).toFixed(1))),
        heat: item.heat,
        risk: item.risk,
        flowPosition: {
          x: 110 + column * 360,
          y: 90 + row * 220,
        },
        blueprintPosition: {
          x: item.blueprintPosition[0],
          y: item.blueprintPosition[1],
        },
        blueprintZone: zoneMeta,
        tags: [zoneMeta?.label, item.asset].filter(Boolean),
      };
    }),
  };
}

const PROFILE_BLUEPRINTS = [
  createProfile({
    id: 'seed-plant',
    label: 'Seed Processing Plant',
    blueprintImage: '/blueprints/manufacturing-plant-with-four-sections.png',
    width: 850,
    height: 700,
    type: 'Agri-processing and dispatch facility',
    description:
      'This blueprint reads as a conveyor-driven seed treatment plant with a long production hall, outdoor material loop, silo bank, dispatch bay, and detached QC / office spine. It is ideal for showing how physical movement, equipment strain, and logistics crossings create visible operational heat.',
    useCases: [
      'Inbound raw seed receiving and initial clean-down',
      'Continuous treatment, dosing, and sampling inside the production hall',
      'Silo staging, dispatch release, and truck / forklift conflicts at the dock',
    ],
    analysis: [
      'The production hall is a dominant central volume, so heat should pool along the auger, cleaner, treater, and cooler path rather than as a uniform blanket.',
      'The QC block is detached from the hall, which creates realistic review latency and back-and-forth traffic during quality holds.',
      'The outdoor dispatch and garden edge create a compelling logistics perimeter where forklift surges and loading delays are obvious on the map.',
    ],
    zones: [
      zone('receiving', 'Receiving', [20, 180, 180, 380]),
      zone('cleaning', 'Cleaning', [170, 260, 390, 430]),
      zone('treatment', 'Treatment Hall', [210, 115, 585, 300]),
      zone('silos', 'Silo Bank', [430, 360, 630, 650]),
      zone('dispatch', 'Dispatch / QC', [610, 60, 825, 260]),
    ],
    triggers: ['equipmentFault', 'forkliftSurge', 'qualityHold', 'congestionSpike'],
    steps: [
      step('Gate inbound truck', 'receiving', 'Inbound truck', [0, 0], [80, 210], 18, 1.1),
      step('Unload seed totes', 'receiving', 'Dock lift', [1, 0], [120, 280], 24, 1.2),
      step('Sample inbound lot', 'dispatch', 'QC bench', [4, 0], [705, 155], 16, 1.0),
      step('Feed auger loop', 'cleaning', 'Auger', [1, 1], [235, 320], 20, 1.3),
      step('Run fine cleaner', 'cleaning', 'Fine cleaner', [2, 1], [285, 285], 22, 1.4),
      step('Debarker inspection', 'cleaning', 'Debarker', [0, 2], [180, 330], 14, 0.9),
      step('Heat-treatment ramp', 'treatment', 'Seed treater', [2, 0], [420, 210], 26, 1.5),
      step('Dose coating chemistry', 'treatment', 'Chemical dosing', [3, 0], [470, 205], 18, 1.4),
      step('Cool treated batch', 'treatment', 'Cooler', [3, 1], [430, 300], 19, 1.1),
      step('Transfer to silo 1', 'silos', 'Silo 1', [3, 2], [490, 420], 21, 1.2),
      step('Balance to silo 2', 'silos', 'Silo 2', [3, 3], [495, 500], 17, 1.0),
      step('Balance to silo 3', 'silos', 'Silo 3', [3, 4], [498, 585], 17, 1.0),
      step('QC release check', 'dispatch', 'QC office', [4, 1], [735, 120], 13, 1.1),
      step('Print dispatch paperwork', 'dispatch', 'Dispatch desk', [4, 2], [710, 85], 11, 0.8),
      step('Stage pallet outbound', 'dispatch', 'Forklift lane', [4, 3], [670, 210], 20, 1.2),
      step('Load outbound truck', 'dispatch', 'Dispatch bay', [4, 4], [695, 45], 23, 1.3),
    ],
  }),
  createProfile({
    id: 'food-plant',
    label: 'Hygienic Food Processing',
    blueprintImage: '/blueprints/blueprint 2.jpg',
    width: 736,
    height: 494,
    type: 'High-care food production facility',
    description:
      'This layout is perfect for contamination, washdown, and packaging simulations. The zone boundaries are explicit: raw handling, primary processing, cooking, hygienic transitions, high-care packaging, lab, and loading.',
    useCases: [
      'Raw material intake through container wash and primary process',
      'Cook, cool, and transfer into pressurized high-care packaging',
      'Quality hold scenarios tied to laboratory review and final store release',
    ],
    analysis: [
      'The raw-to-hygienic transition is the core operational story; every trigger should intensify around those corridor thresholds.',
      'The pressurized packaging and high-care area create a natural hotspot for queueing and contamination sensitivity.',
      'Loading sits far to the right, so failures upstream should visually propagate as a long tail of delayed occupancy.',
    ],
    zones: [
      zone('raw', 'Raw Handling', [90, 105, 230, 245]),
      zone('primary', 'Primary Processing', [240, 80, 430, 205]),
      zone('cook', 'Cooking', [270, 220, 430, 330]),
      zone('high-care', 'High Care', [420, 220, 605, 350]),
      zone('packaging', 'Packaging', [430, 95, 610, 210]),
      zone('loading', 'Loading', [610, 160, 715, 340]),
    ],
    triggers: ['contaminationAlert', 'qualityHold', 'congestionSpike', 'rushOrder'],
    steps: [
      step('Receive chilled ingredients', 'raw', 'Raw materials dock', [0, 0], [170, 190], 18, 1.0),
      step('Open and inspect totes', 'raw', 'Raw handling bench', [1, 0], [215, 165], 15, 0.9),
      step('Container wash release', 'raw', 'Container wash', [1, 1], [215, 245], 19, 1.1),
      step('Primary grind start', 'primary', 'Primary grinder', [2, 0], [325, 155], 24, 1.4),
      step('Ingredient dosing', 'primary', 'Ingredient feeder', [1, 2], [250, 125], 17, 1.1),
      step('Cook batch to target', 'cook', 'Cook line', [2, 1], [330, 270], 26, 1.4),
      step('Thermal record verify', 'cook', 'Cook log station', [2, 2], [365, 300], 12, 0.9),
      step('Hygienic transfer gate', 'high-care', 'Airlock transition', [3, 1], [455, 285], 15, 1.3),
      step('Metal detection prep', 'packaging', 'Metal detector', [3, 0], [520, 165], 14, 1.2),
      step('Pressurized fill run', 'packaging', 'Packaging line', [4, 0], [545, 145], 23, 1.4),
      step('Seal integrity check', 'packaging', 'Seal check station', [4, 1], [555, 185], 16, 1.1),
      step('High-care palletize', 'high-care', 'Palletizing cell', [4, 2], [520, 300], 18, 1.2),
      step('Laboratory sample release', 'high-care', 'Laboratory handoff', [3, 2], [505, 360], 13, 1.0),
      step('Move to final store', 'loading', 'Final store lane', [5, 1], [655, 205], 18, 1.1),
      step('Dispatch load sequence', 'loading', 'Loading bay', [5, 2], [675, 270], 20, 1.2),
      step('Waste & hygiene closeout', 'cook', 'Hygiene facilities', [2, 3], [315, 345], 11, 0.8),
    ],
  }),
  createProfile({
    id: 'restaurant-overall',
    label: 'Restaurant Overall Plan',
    blueprintImage: '/blueprints/blueprint 3.png',
    width: 937,
    height: 756,
    type: 'Front-of-house and kitchen service orchestration',
    description:
      'This overall floor plan supports a service-focused SOP: receiving, prep, line work, bar fulfillment, host flow, and dining room service. It is excellent for showing how service pressure creates heat in both back-of-house and guest-facing spaces.',
    useCases: [
      'Lunch rush order routing from alley receiving through prep and pass',
      'Dining-room service load balancing between host stand, bar, and server stations',
      'Food safety holds interacting with guest throughput',
    ],
    analysis: [
      'The service spine between kitchen and dining is the main kinetic corridor; most heat should accumulate along that edge rather than in the center of the dining room.',
      'The broad dining floor creates a good contrast between ambient guest occupancy and concentrated operational hotspots.',
      'Receiving and back-of-house storage are separated from the guest entry, allowing clear storylines for rush orders versus hospitality flow.',
    ],
    zones: [
      zone('receiving', 'Receiving / Storage', [40, 110, 250, 355]),
      zone('prep', 'Kitchen Prep', [230, 165, 425, 395]),
      zone('line', 'Cook Line / Expo', [370, 220, 540, 430]),
      zone('bar', 'Service Bar', [470, 360, 635, 560]),
      zone('dining', 'Dining Floor', [560, 260, 885, 665]),
      zone('host', 'Host / Entry', [690, 120, 900, 250]),
    ],
    triggers: ['rushOrder', 'qualityHold', 'congestionSpike'],
    steps: [
      step('Receive alley delivery', 'receiving', 'Receiving dock', [0, 1], [120, 285], 12, 0.8),
      step('Store dry inventory', 'receiving', 'Dry storage', [0, 0], [150, 160], 14, 0.9),
      step('Pull prep requisition', 'prep', 'Prep table', [1, 0], [295, 220], 10, 0.8),
      step('Cold station mise en place', 'prep', 'Cold prep', [1, 1], [305, 300], 16, 1.0),
      step('Hot line fire ticket', 'line', 'Cook line', [2, 1], [470, 300], 18, 1.2),
      step('Expo plate check', 'line', 'Expo pass', [2, 2], [505, 360], 10, 1.0),
      step('Bar beverage queue', 'bar', 'Service bar', [3, 2], [560, 420], 14, 1.1),
      step('Host seats walk-in', 'host', 'Host stand', [4, 0], [785, 165], 9, 0.7),
      step('Server route to patio edge', 'dining', 'Dining aisle', [4, 1], [720, 360], 13, 0.9),
      step('Deliver first course', 'dining', 'Table service', [4, 2], [780, 460], 12, 0.8),
      step('Collect guest feedback', 'dining', 'Dining floor', [4, 3], [690, 545], 9, 0.7),
      step('Refire kitchen correction', 'line', 'Cook line', [3, 1], [455, 270], 15, 1.2),
      step('Dessert prep pickup', 'prep', 'Dessert station', [2, 3], [390, 430], 11, 0.8),
      step('Final table closeout', 'dining', 'POS close', [5, 3], [825, 575], 10, 0.6),
      step('Reset dining section', 'dining', 'Bus station', [5, 4], [860, 640], 13, 0.9),
      step('End-of-shift sanitation', 'prep', 'Sanitation sink', [1, 3], [270, 500], 14, 1.0),
    ],
  }),
  createProfile({
    id: 'restaurant-ops',
    label: 'Restaurant Back-Bar Operations',
    blueprintImage: '/blueprints/blueprint 4.png',
    width: 1200,
    height: 881,
    type: 'Detailed bar, kitchen, and patio service choreography',
    description:
      'This enlarged restaurant plan provides a more tactical service simulation than the overall floor plan. It captures dish return, back-bar prep, line coordination, bar queues, patio delivery, and detailed station crossings.',
    useCases: [
      'Dinner service choreography across bar, expo, and patio seating',
      'Back-bar bottlenecks that spill into dining and dish return',
      'Critical utility or cleanup triggers in a tightly coupled service space',
    ],
    analysis: [
      'Because the plan is detailed, the heatmap should emphasize micro-clusters at sinks, prep counters, bar wells, and the patio service edge.',
      'The back-bar and dish return loop can create a high-frequency circulation ring that looks very different from the slower dining field.',
      'The patio edge is useful for simulating how service demand fans out away from the kitchen core.',
    ],
    zones: [
      zone('dish', 'Dish / Return', [130, 195, 350, 455]),
      zone('prep', 'Kitchen Prep', [245, 300, 455, 560]),
      zone('expo', 'Expo / Pass', [430, 330, 615, 515]),
      zone('bar', 'Back Bar', [520, 445, 760, 635]),
      zone('patio', 'Patio Service', [735, 350, 1105, 770]),
      zone('storage', 'Cold Storage', [105, 520, 270, 760]),
    ],
    triggers: ['rushOrder', 'congestionSpike', 'equipmentFault', 'qualityHold'],
    steps: [
      step('Receive beverage restock', 'storage', 'Walk-in cooler', [0, 3], [190, 620], 12, 0.9),
      step('Dish return sweep', 'dish', 'Dish station', [0, 1], [205, 335], 14, 1.0),
      step('Glassware polish', 'bar', 'Glass rail', [2, 2], [610, 515], 10, 0.7),
      step('Cold garnish prep', 'prep', 'Prep counter', [1, 1], [345, 395], 13, 0.9),
      step('Hot pickup fire', 'expo', 'Expo shelf', [2, 1], [510, 385], 15, 1.1),
      step('Cocktail queue build', 'bar', 'Bar well', [3, 1], [680, 495], 18, 1.2),
      step('Patio runner dispatch', 'patio', 'Patio aisle', [4, 1], [830, 510], 14, 0.9),
      step('Table check-in', 'patio', 'Patio tables', [4, 2], [930, 590], 10, 0.7),
      step('Refill back-bar ice', 'bar', 'Ice well', [3, 2], [640, 575], 9, 0.7),
      step('Dish machine unload', 'dish', 'Dish machine', [1, 2], [270, 410], 12, 1.0),
      step('Replate quality correction', 'expo', 'Expo pass', [2, 3], [555, 455], 13, 1.0),
      step('VIP rush fire', 'expo', 'Rush ticket rail', [3, 0], [520, 340], 12, 1.2),
      step('Patio delivery sprint', 'patio', 'Service lane', [5, 1], [1005, 500], 11, 0.8),
      step('Close guest check', 'patio', 'POS handheld', [5, 2], [970, 655], 10, 0.6),
      step('Restock station reset', 'storage', 'Dry shelf', [1, 4], [165, 700], 13, 0.8),
      step('Final sanitation loop', 'dish', 'Sanitation sink', [0, 4], [230, 520], 16, 1.0),
    ],
  }),
  createProfile({
    id: 'machine-shop',
    label: 'Precision Machine Shop',
    blueprintImage: '/blueprints/blueprint 5.jpg',
    width: 1920,
    height: 1000,
    type: 'Discrete manufacturing and material-flow floor',
    description:
      'This blueprint is a classic machining hall with receiving, large work cells, inspection islands, material staging, and shipment flow. It is the strongest blueprint for a capstone story around simulation, because travel, queues, strain, and dispatch are physically legible.',
    useCases: [
      'Material receipt, machining cell progression, and inspection release',
      'Forklift traffic interacting with operators at shared aisles',
      'Equipment fault, staffing pressure, and expedited shipment triggers',
    ],
    analysis: [
      'The hall is wide and open, so hotspots should form around machine clusters and the shared logistics spine rather than along walls.',
      'Receiving and dispatch are spatially separate, which makes backlog propagation easy to read on a heatmap.',
      'This layout supports the best digital twin narrative because the same SOP can be understood as both a process graph and a physical machine hall.',
    ],
    zones: [
      zone('receiving', 'Receiving', [180, 620, 720, 930]),
      zone('machining', 'Machining Cells', [420, 120, 1440, 560]),
      zone('inspection', 'Inspection', [1220, 280, 1560, 520]),
      zone('assembly', 'Assembly / Bench', [760, 620, 1220, 900]),
      zone('dispatch', 'Dispatch', [1540, 180, 1860, 520]),
      zone('support', 'Support / Utilities', [145, 90, 440, 350]),
    ],
    triggers: ['equipmentFault', 'forkliftSurge', 'rushOrder', 'congestionSpike'],
    steps: [
      step('Receive steel plate', 'receiving', 'Inbound truck', [0, 3], [520, 760], 18, 1.0),
      step('Forklift to staging', 'receiving', 'Forklift lane', [1, 3], [735, 770], 16, 1.1),
      step('Cut blank on saw', 'support', 'Saw station', [1, 0], [365, 225], 20, 1.2),
      step('Move blank to mill', 'machining', 'Transfer cart', [2, 0], [660, 240], 13, 0.9),
      step('Mill datum faces', 'machining', 'Mill cell A', [2, 1], [760, 285], 24, 1.4),
      step('CNC turning pass', 'machining', 'Lathe cell', [3, 1], [975, 260], 22, 1.3),
      step('Deburr and wash', 'assembly', 'Wash bench', [3, 3], [980, 735], 16, 1.0),
      step('Secondary mill op', 'machining', 'Mill cell B', [4, 1], [1180, 270], 21, 1.3),
      step('Probe verification', 'inspection', 'CMM island', [5, 1], [1340, 330], 17, 1.2),
      step('Manual gauge check', 'inspection', 'Gauge bench', [5, 2], [1455, 405], 14, 1.0),
      step('Bench assembly fit', 'assembly', 'Assembly bench', [4, 3], [1080, 760], 18, 1.0),
      step('Rework polish', 'assembly', 'Hand finishing', [5, 3], [875, 840], 12, 0.9),
      step('Pack finished unit', 'dispatch', 'Packing station', [6, 2], [1690, 355], 16, 1.0),
      step('Print traveler and label', 'dispatch', 'Dispatch desk', [6, 1], [1620, 260], 11, 0.7),
      step('Stage outbound crate', 'dispatch', 'Outbound staging', [7, 2], [1765, 430], 15, 1.0),
      step('Load shipment truck', 'dispatch', 'Truck bay', [7, 1], [1760, 255], 19, 1.1),
    ],
  }),
];

function hashText(value) {
  const text = String(value || 'vision-sop');
  let hash = 0;
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash << 5) - hash + text.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash);
}

function normalizeValue(value) {
  return Math.min(1, Math.max(0, Number(value ?? 0) / 100));
}

export function listSimulationProfiles() {
  return PROFILE_BLUEPRINTS;
}

export function getSimulationProfile(sop, explicitProfileId = null) {
  if (explicitProfileId) {
    return PROFILE_BLUEPRINTS.find((profile) => profile.id === explicitProfileId) || PROFILE_BLUEPRINTS[0];
  }

  const title = String(sop?.title || '').toLowerCase();
  const station = String(sop?.station || '').toLowerCase();
  const text = `${title} ${station}`;

  const keywordMatch = PROFILE_BLUEPRINTS.find((profile) => {
    if (profile.id === 'seed-plant') return /seed|dispatch|treat/i.test(text);
    if (profile.id === 'food-plant') return /food|cook|hygiene|pack/i.test(text);
    if (profile.id === 'restaurant-overall') return /service|guest|dining|host/i.test(text);
    if (profile.id === 'restaurant-ops') return /bar|patio|dish|expo/i.test(text);
    if (profile.id === 'machine-shop') return /assembly|machine|part|shop|qa/i.test(text);
    return false;
  });

  if (keywordMatch) {
    return keywordMatch;
  }

  const fallbackIndex = hashText(sop?.id || sop?.title || sop?.station) % PROFILE_BLUEPRINTS.length;
  return PROFILE_BLUEPRINTS[fallbackIndex];
}

export function getDefaultImpacts() {
  return Object.fromEntries(IMPACT_CONTROLS.map((control) => [control.id, control.defaultValue]));
}

export function getImpactControls() {
  return IMPACT_CONTROLS;
}

export function getTriggerDefinitions(profile) {
  const resolvedProfile = typeof profile === 'string'
    ? PROFILE_BLUEPRINTS.find((item) => item.id === profile)
    : profile;

  const triggerIds = resolvedProfile?.triggers || [];
  return triggerIds.map((triggerId) => TRIGGER_LIBRARY[triggerId]).filter(Boolean);
}

export function getDefaultTriggers(profile) {
  return Object.fromEntries(getTriggerDefinitions(profile).map((trigger) => [trigger.id, false]));
}

export function materializeSimulationSteps(sop, options = {}) {
  const profile = getSimulationProfile(sop, options.profileId);
  const impacts = {
    ...getDefaultImpacts(),
    ...(options.impacts || {}),
  };
  const triggers = {
    ...getDefaultTriggers(profile),
    ...(options.triggers || {}),
  };

  const throughput = normalizeValue(impacts.throughputPressure);
  const staffingGap = 1 - normalizeValue(impacts.staffingLevel);
  const equipmentStrain = normalizeValue(impacts.equipmentStrain);
  const safetySensitivity = normalizeValue(impacts.safetySensitivity);
  const qualitySensitivity = normalizeValue(impacts.qualitySensitivity);

  const durationPressure = 1 + throughput * 0.28 + staffingGap * 0.16 + (triggers.rushOrder ? 0.18 : 0) + (triggers.congestionSpike ? 0.09 : 0);
  const heatPressure = 1 + throughput * 0.22 + equipmentStrain * 0.24 + (triggers.forkliftSurge ? 0.18 : 0) + (triggers.congestionSpike ? 0.13 : 0) + (triggers.contaminationAlert ? 0.14 : 0);
  const qualityPressure = qualitySensitivity * 0.25 + (triggers.qualityHold ? 0.22 : 0) + (triggers.contaminationAlert ? 0.18 : 0);
  const riskPressure = safetySensitivity * 0.2 + equipmentStrain * 0.16 + (triggers.equipmentFault ? 0.24 : 0);

  return profile.steps.map((stepItem, index) => ({
    ...stepItem,
    order: index,
    step_index: index,
    target_duration_s: Number((stepItem.target_duration_s * durationPressure).toFixed(1)),
    heat: Number((stepItem.heat * heatPressure + qualityPressure * 0.8).toFixed(2)),
    risk: Number(Math.min(1, stepItem.risk + riskPressure).toFixed(2)),
    dependencies: index === 0 ? [] : [profile.steps[index - 1].id],
  }));
}


export function buildSessionSimulationPreset(session, summary, alerts = [], ergonomics = null, muda = null) {
  const criticalAlerts = alerts.filter((alert) => String(alert.severity || '').toLowerCase() === 'critical').length;
  const deviation = Math.max(0, Number(session?.deviation_score || 0));
  const moveFraction = Math.max(0, Number(muda?.move_fraction || 0));
  const idleFraction = Math.max(0, Number(muda?.idle_fraction || 0));
  const ergoScore = Math.max(0, Number(ergonomics?.score || 0));
  const skipped = summary?.skipped_steps?.length || 0;
  const extra = summary?.extra_steps?.length || 0;

  return {
    impacts: {
      throughputPressure: Math.min(100, Math.round(48 + deviation * 55 + extra * 8 + moveFraction * 30)),
      staffingLevel: Math.max(25, Math.round(88 - idleFraction * 35 - moveFraction * 20 - skipped * 5)),
      equipmentStrain: Math.min(100, Math.round(34 + alerts.length * 7 + deviation * 28)),
      safetySensitivity: Math.min(100, Math.round(42 + criticalAlerts * 14 + Math.max(0, 70 - ergoScore) * 0.5)),
      qualitySensitivity: Math.min(100, Math.round(46 + skipped * 14 + deviation * 20)),
    },
    triggers: {
      equipmentFault: criticalAlerts > 0 || alerts.length >= 2,
      congestionSpike: moveFraction > 0.22 || extra > 0,
      qualityHold: skipped > 0,
      contaminationAlert: (ergonomics?.hotspots || []).some((item) => /care|cook|wash|quality/i.test(String(item.area || item.message || ''))),
      forkliftSurge: (summary?.extra_steps || []).some((item) => /move|transport|load/i.test(String(item))),
      rushOrder: deviation > 0.2 || Number(session?.cycle_time_s || 0) > 75,
    },
  };
}
export function getScenarioSummary(sop, options = {}) {
  const profile = getSimulationProfile(sop, options.profileId);
  const steps = materializeSimulationSteps(sop, options);

  return {
    id: profile.id,
    label: profile.label,
    type: profile.type,
    description: profile.description,
    analysis: profile.analysis,
    useCases: profile.useCases,
    blueprintImage: profile.blueprintImage,
    totalSteps: steps.length,
    zones: profile.zones,
    assets: Array.from(new Set(steps.map((stepItem) => stepItem.asset))),
    triggers: getTriggerDefinitions(profile),
    width: profile.width,
    height: profile.height,
  };
}


