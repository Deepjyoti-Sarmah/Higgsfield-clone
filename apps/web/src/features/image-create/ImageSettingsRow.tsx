import type { ReactNode } from "react"
import type { ImageOptions } from "../../api/imageOptions"
import { imageCreateCopy } from "./imageCreateCopy"
import type { ImageSettingsControls } from "./imageCreateTypes"

type ImageSettingsRowProps = {
  options: ImageOptions
  settings: ImageSettingsControls
}

type GroupProps = {
  options: ImageOptions
  settings: ImageSettingsControls
}

const chipClasses =
  "cursor-pointer rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-text " +
  "peer-checked:border-accent peer-checked:text-accent peer-focus-visible:outline-2 " +
  "peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent"

type ChipProps<T extends string> = {
  name: string
  value: T
  label: string
  checked: boolean
  onSelect: (value: T) => void
}

function Chip<T extends string>({ name, value, label, checked, onSelect }: ChipProps<T>) {
  return (
    <label className="inline-flex">
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        onChange={() => onSelect(value)}
        className="peer sr-only"
      />
      <span className={chipClasses}>{label}</span>
    </label>
  )
}

function Group({ legend, children }: { legend: string; children: ReactNode }) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="text-sm text-muted">{legend}</legend>
      <div className="flex flex-wrap gap-2">{children}</div>
    </fieldset>
  )
}

function AspectGroup({ options, settings }: GroupProps) {
  const copy = imageCreateCopy.settings
  return (
    <Group legend={copy.aspectLabel}>
      {options.aspect_ratios.map((value) => (
        <Chip
          key={value}
          name="aspect-ratio"
          value={value}
          label={copy.aspectLabels[value]}
          checked={settings.settings.aspectRatio === value}
          onSelect={settings.setAspectRatio}
        />
      ))}
    </Group>
  )
}

function QualityGroup({ options, settings }: GroupProps) {
  const copy = imageCreateCopy.settings
  return (
    <Group legend={copy.qualityLabel}>
      {options.qualities.map((value) => (
        <Chip
          key={value}
          name="quality"
          value={value}
          label={copy.qualityLabels[value]}
          checked={settings.settings.quality === value}
          onSelect={settings.setQuality}
        />
      ))}
    </Group>
  )
}

function CountGroup({ options, settings }: GroupProps) {
  const copy = imageCreateCopy.settings
  const counts = Array.from({ length: options.max_count }, (_, index) => index + 1)
  return (
    <Group legend={copy.countLabel}>
      {counts.map((value) => (
        <Chip
          key={value}
          name="count"
          value={String(value)}
          label={copy.countValue(value)}
          checked={settings.settings.count === value}
          onSelect={(next) => settings.setCount(Number(next))}
        />
      ))}
    </Group>
  )
}

export function ImageSettingsRow({ options, settings }: ImageSettingsRowProps) {
  return (
    <div className="flex flex-wrap gap-6">
      <AspectGroup options={options} settings={settings} />
      <QualityGroup options={options} settings={settings} />
      <CountGroup options={options} settings={settings} />
    </div>
  )
}
