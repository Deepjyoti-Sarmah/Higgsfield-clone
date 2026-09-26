// Copy in the §9 film-editing voice; short, concrete, sentence case.
export const sequenceCopy = {
  strip: {
    emptySlot: "Add a clip from the rail",
    removeShot: (position: number) => `Remove shot ${position}`,
    moveLeft: (position: number) => `Move shot ${position} left`,
    moveRight: (position: number) => `Move shot ${position} right`,
    trimStartEarlier: (position: number) => `Shot ${position}: start earlier`,
    trimStartLater: (position: number) => `Shot ${position}: start later`,
    trimEndEarlier: (position: number) => `Shot ${position}: end earlier`,
    trimEndLater: (position: number) => `Shot ${position}: end later`,
  },
  transitions: {
    cut: { label: "CUT", name: "Cut" },
    crossfade: { label: "XFADE", name: "Crossfade" },
    fade_black: { label: "FADE", name: "Fade to black" },
  },
  picker: {
    heading: "Your clips",
    add: "Add",
    added: "Added",
    differentShape: (ratio: string) => `Different shape: ${ratio}`,
  },
  music: {
    heading: "Music",
    hint: "Drop an mp3, m4a or wav here, up to 10 MB.",
    silent: "Silent. Clip audio is not used.",
    remove: "Remove music",
    browse: "Choose a file",
  },
  total: {
    label: "about",
  },
  render: {
    button: "Render · 1 credit",
    needTwoClips: "Add one more clip to render.",
    uploading: "Wait for the music to finish uploading.",
    clipInvalid: "One of these clips can't be used any more. Remove it and try again.",
    limit: "That's today's job limit. It resets at midnight UTC.",
    failed: "The render didn't start. Try again.",
  },
} as const
