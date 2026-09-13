// The design seals the title with a middle dot; the escape keeps this file ASCII.
export function documentTitle(name: string): string {
  return `${name} \u00b7 Higgsfield`
}

export const shareCopy = {
  page: {
    attribution: "Made with Higgsfield",
    cta: "Make your own",
    ctaHref: "/",
    documentTitle,
  },
  states: {
    loading: {
      srText: "Loading this video",
    },
    error: {
      title: "We couldn't load this video.",
      body: "Check your connection and try again.",
      action: "Retry",
    },
    notFound: {
      title: "This video doesn't exist or was removed.",
      body: "Check the link, or make your own.",
      action: "Make your own",
    },
    notReady: {
      title: "Still generating.",
      body: "This video isn't ready yet. Check back in a moment.",
      action: "Refresh",
    },
    failed: {
      title: "This video didn't finish.",
      body: "Something went wrong while it was being generated.",
      action: "Make your own",
    },
  },
  result: {
    download: "Download",
  },
}
