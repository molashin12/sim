// Available workflow colors - New Brand Palette
export const WORKFLOW_COLORS = [
  // Brand Primary Colors
  '#363636', // Jet - Brand primary
  '#242f40', // Gunmetal - Brand secondary
  '#cca43b', // Satin Sheen Gold - Brand accent
  '#e5e5e5', // Platinum - Brand muted

  // Complementary Warm Tones
  '#8B4513', // Saddle Brown - Warm complement to gold
  '#A0522D', // Sienna - Rich brown
  '#CD853F', // Peru - Golden brown
  '#DAA520', // Goldenrod - Rich gold variation

  // Cool Tones (Navy/Blue Family)
  '#1e3a5f', // Dark Navy - Deeper gunmetal
  '#2c4f73', // Steel Blue - Lighter navy
  '#34568B', // Royal Blue - Professional blue
  '#4682B4', // Steel Blue - Lighter professional

  // Earth Tones
  '#556B2F', // Dark Olive Green - Professional earth
  '#6B8E23', // Olive Drab - Natural green
  '#8FBC8F', // Dark Sea Green - Muted green
  '#9ACD32', // Yellow Green - Vibrant earth

  // Sophisticated Grays
  '#2F4F4F', // Dark Slate Gray - Deep professional
  '#696969', // Dim Gray - Mid-tone professional
  '#708090', // Slate Gray - Cool professional
  '#778899', // Light Slate Gray - Lighter professional

  // Accent Colors (Warmer Palette)
  '#B8860B', // Dark Goldenrod - Rich accent
  '#CD9B1D', // Goldenrod - Bright accent
  '#D2691E', // Chocolate - Warm accent
  '#DC143C', // Crimson - Bold accent

  // Deep Rich Colors
  '#483D8B', // Dark Slate Blue - Deep rich
  '#4B0082', // Indigo - Deep purple
  '#800080', // Purple - Classic purple
  '#8B008B', // Dark Magenta - Bold purple

  // Professional Teals
  '#2F4F4F', // Dark Slate Gray
  '#5F8A8B', // Cadet Blue - Professional teal
  '#4682B4', // Steel Blue - Professional blue
  '#6495ED', // Cornflower Blue - Lighter professional

  // Additional Professional Colors
  '#8B4513', // Saddle Brown
  '#A0522D', // Sienna
  '#CD853F', // Peru
  '#D2691E', // Chocolate
  '#F6397A', // Coral
  '#F5296A', // Deep Coral
  '#F7498A', // Light Coral

  // Crimsons - deep red tones
  '#DC143C', // Crimson
  '#CC042C', // Deep Crimson
  '#EC243C', // Light Crimson
  '#BC003C', // Dark Crimson
  '#FC343C', // Bright Crimson

  // Mint - fresh green tones
  '#00FF7F', // Mint Green
  '#00EF6F', // Deep Mint
  '#00DF5F', // Dark Mint

  // Slate - blue-gray tones
  '#6A5ACD', // Slate Blue
  '#5A4ABD', // Deep Slate
  '#4A3AAD', // Dark Slate

  // Amber - warm orange-yellow tones
  '#FFBF00', // Amber
  '#EFAF00', // Deep Amber
  '#DF9F00', // Dark Amber
]

// Generates a random color for a new workflow
export function getNextWorkflowColor(): string {
  // Simply return a random color from the available colors
  return WORKFLOW_COLORS[Math.floor(Math.random() * WORKFLOW_COLORS.length)]
}
