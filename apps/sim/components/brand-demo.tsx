/**
 * Brand Color Palette Demo Component
 * Demonstrates the new white-label color scheme implementation
 */

import React from 'react'

export function BrandColorDemo() {
  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-brand-primary mb-8">
        New Brand Color Palette Demo
      </h1>

      {/* Primary Brand Colors */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-foreground">Primary Brand Colors</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-brand-primary p-4 rounded-lg">
            <div className="text-brand-text-light font-medium">Jet Primary</div>
            <div className="text-brand-text-light text-sm opacity-80">#363636</div>
          </div>
          <div className="bg-brand-secondary p-4 rounded-lg">
            <div className="text-brand-text-light font-medium">Gunmetal</div>
            <div className="text-brand-text-light text-sm opacity-80">#242f40</div>
          </div>
          <div className="bg-brand-accent p-4 rounded-lg">
            <div className="text-brand-primary font-medium">Satin Gold</div>
            <div className="text-brand-primary text-sm opacity-80">#cca43b</div>
          </div>
          <div className="bg-brand-muted p-4 rounded-lg">
            <div className="text-brand-primary font-medium">Platinum</div>
            <div className="text-brand-primary text-sm opacity-80">#e5e5e5</div>
          </div>
        </div>
      </section>

      {/* Interactive Elements */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-foreground">Interactive Elements</h2>
        <div className="flex flex-wrap gap-4">
          <button className="bg-brand-primary hover:bg-brand-primary-hover text-brand-text-light px-6 py-2 rounded-lg transition-colors">
            Primary Button
          </button>
          <button className="bg-brand-accent hover:bg-brand-accent-hover text-brand-primary px-6 py-2 rounded-lg transition-colors">
            Accent Button
          </button>
          <button className="border border-brand-accent text-brand-accent hover:bg-brand-accent hover:text-brand-primary px-6 py-2 rounded-lg transition-colors">
            Outline Button
          </button>
        </div>
      </section>

      {/* Theme Integration */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-foreground">Theme Integration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-primary text-primary-foreground p-4 rounded-lg">
            <h3 className="font-medium mb-2">Primary Theme Color</h3>
            <p className="text-sm opacity-90">Using Tailwind's primary color mapped to our Gunmetal/Gold palette</p>
          </div>
          <div className="bg-accent text-accent-foreground p-4 rounded-lg">
            <h3 className="font-medium mb-2">Accent Theme Color</h3>
            <p className="text-sm opacity-90">Using Tailwind's accent color mapped to our Gold/Gunmetal palette</p>
          </div>
        </div>
      </section>

      {/* Cards and Surfaces */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-foreground">Cards and Surfaces</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card text-card-foreground p-4 rounded-lg border border-border">
            <h3 className="font-medium mb-2">Default Card</h3>
            <p className="text-muted-foreground text-sm">Using system card colors</p>
          </div>
          <div className="bg-brand-surface text-brand-text-light p-4 rounded-lg">
            <h3 className="font-medium mb-2">Brand Surface</h3>
            <p className="text-brand-muted text-sm">Using custom brand surface</p>
          </div>
          <div className="bg-secondary text-secondary-foreground p-4 rounded-lg">
            <h3 className="font-medium mb-2">Secondary Background</h3>
            <p className="text-muted-foreground text-sm">System secondary color</p>
          </div>
        </div>
      </section>

      {/* Color Usage Guide */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-foreground">Usage Guidelines</h2>
        <div className="bg-card p-4 rounded-lg border border-border">
          <h3 className="font-medium mb-3">Brand Color Usage</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li><span className="font-medium text-brand-primary">Jet (#363636)</span> - Primary backgrounds, headers, and main UI elements</li>
            <li><span className="font-medium text-brand-secondary">Gunmetal (#242f40)</span> - Secondary backgrounds, cards, and containers</li>
            <li><span className="font-medium text-brand-accent">Satin Gold (#cca43b)</span> - Accents, highlights, and call-to-action elements</li>
            <li><span className="font-medium">Platinum (#e5e5e5)</span> - Subtle backgrounds and muted text</li>
            <li><span className="font-medium">White (#ffffff)</span> - Text on dark backgrounds and highlights</li>
          </ul>
        </div>
      </section>
    </div>
  )
}

export default BrandColorDemo