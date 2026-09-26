// Copy in the §9 film-editing voice; short, concrete, sentence case.
export const sequenceCopy = {
  steps: {
    add: {
      number: "1",
      heading: "Add videos",
      body: "Pick finished clips below. Need one first? Make it in Clip.",
    },
    arrange: {
      number: "2",
      heading: "Arrange & trim",
      body: "Drag to reorder. Trim the start and end in seconds.",
    },
    music: {
      number: "3",
      heading: "Music (optional)",
      body: "Drop a track, or leave it silent.",
    },
    render: {
      number: "4",
      heading: "Render & export",
      body: "Render the film, then download, share, or face-swap it.",
    },
  },
  strip: {
    emptySlot: "Shot goes here — add a clip in step 1",
    removeShot: (position: number) => `Remove shot ${position}`,
    moveLeft: (position: number) => `Move shot ${position} left`,
    moveRight: (position: number) => `Move shot ${position} right`,
    shotLabel: (position: number, total: number) => `Shot ${position} of ${total}`,
  },
  trim: {
    stepNote: "Each tap moves 0.5 seconds.",
    startEarlier: (position: number) => `Shot ${position}: move the start 0.5 seconds earlier`,
    startLater: (position: number) => `Shot ${position}: move the start 0.5 seconds later`,
    endEarlier: (position: number) => `Shot ${position}: move the end 0.5 seconds earlier`,
    endLater: (position: number) => `Shot ${position}: move the end 0.5 seconds later`,
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
    hint: "Finished clips from your rail. Add at least two.",
    stageHint: "Tip: open any finished clip above and choose “Add to sequence”.",
    emptyTitle: "No clips yet",
    emptyBody: "Make one in Clip (animate a still). Your own footage comes in through the Clip tab for now.",
    goToClip: "Go to Clip",
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
  exportGuide: {
    heading: "What happens next",
    started: "Your film is rendering. It opens in your rail when it's done.",
    download: "Download it straight from the rail.",
    share: "Share it from the rail with a link.",
    faceswap: "To swap a face into it, open the finished film and use it as a face swap target.",
  },
} as const
