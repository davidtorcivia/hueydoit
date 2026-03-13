export const ruleTemplates = [
  {
    id: 'holiday_colors',
    name: 'Holiday Colors',
    description: 'Automatically cycle through the active holiday\'s color palette',
    icon: '🎄',
    rule: {
      name: 'Holiday Colors',
      priority: 20,
      enabled: true,
      config: {
        condition: {
          provider: 'holiday',
          match: { active_holiday: { gt: '' } },
        },
        effect: {
          mode: 'cycle',
          colors: ['#ff0000', '#00ff00'],
          brightness: 80,
          transition: 1000,
          cycle_interval: 30,
          use_holiday_colors: true,
        },
        targets: [],
      },
    },
  },
  {
    id: 'night_mode',
    name: 'Night Mode',
    description: 'Warm dim light after sunset',
    icon: '🌙',
    rule: {
      name: 'Night Mode',
      priority: 50,
      enabled: true,
      config: {
        condition: {
          provider: 'solar',
          match: { period: 'night' },
        },
        effect: {
          mode: 'static',
          colors: ['#ff8c00'],
          brightness: 30,
          transition: 5000,
        },
        targets: [],
      },
    },
  },
  {
    id: 'cold_alert',
    name: 'Cold Alert',
    description: 'Blue lights when temperature drops below freezing',
    icon: '❄️',
    rule: {
      name: 'Cold Alert',
      priority: 30,
      enabled: true,
      config: {
        condition: {
          provider: 'weather',
          match: { temp_f: { lte: 32 } },
        },
        effect: {
          mode: 'static',
          colors: ['#4488ff'],
          brightness: 60,
          transition: 2000,
        },
        targets: [],
      },
    },
  },
  {
    id: 'evening_lights',
    name: 'Evening Lights',
    description: 'Lights on during evening hours (6 PM - 11 PM)',
    icon: '💡',
    rule: {
      name: 'Evening Lights',
      priority: 60,
      enabled: true,
      config: {
        condition: {
          provider: 'time',
          match: { hour: { gte: 18 } },
        },
        effect: {
          mode: 'static',
          colors: ['#ffeedd'],
          brightness: 70,
          transition: 3000,
        },
        targets: [],
      },
    },
  },
];
