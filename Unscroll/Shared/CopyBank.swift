import Foundation

/// Every nudge line, keyed by voice and ladder level (NudgeLadder.dc.html).
///
/// House rules: never a sound, numbers are always true, tease then help, never shame,
/// leaving is the win we celebrate. Distances come from `Odometer` and are always
/// described as approximate ("about").
///
/// Tokens: {visit} {app} {elapsed} {distance} {landmark}
enum CopyBank {
    struct Context {
        var visit: Int = 1
        var app: String = "this app"
        var elapsedSeconds: Int = 0

        var metres: Double { Odometer.metres(seconds: elapsedSeconds) }
    }

    static let lines: [Voice: [NudgeLevel: [String]]] = [
        .gentle: [
            .arrive: [
                "Visit {visit}. Hi, nice to see you.",
                "Visit {visit} today. Just checking in.",
                "Visit {visit}. Take what you came for, then go easy.",
                "Hello again. That's visit {visit}.",
                "Visit {visit}. Breathe first, scroll second.",
                "Visit {visit}. I'll keep you company for a bit.",
            ],
            .notice: [
                "{elapsed} in. How are you feeling?",
                "Hey, it's been {elapsed}. Maybe a little break?",
                "{elapsed} so far. Is this still the good part?",
                "{elapsed} in {app}. A sip of water might feel nice.",
                "Just a soft tap: {elapsed} in {app}.",
                "{elapsed} in. You're allowed to stop whenever.",
            ],
            .nudge: [
                "{elapsed} now. Your thumb has travelled about {distance}. Rest it?",
                "It's been {elapsed}. Maybe look up for a moment?",
                "{elapsed} in {app}. A stretch could feel good right now.",
                "That's {landmark} of scrolling. A gentle pause?",
                "{elapsed}. Whatever you're looking for might not be in there.",
                "Still here after {elapsed}. Want to try a short break?",
            ],
            .shield: [
                "You've reached the limit you set. Be kind to yourself.",
                "That's your limit for today. Something calmer next?",
                "Limit reached. You set this for a good reason.",
                "Time's up for today. Your evening will thank you.",
                "You hit your limit. Maybe a short walk?",
                "That's enough for today. Well done for noticing.",
            ],
        ],
        .witty: [
            .arrive: [
                // Seeded by visit count: visit 7 reads "Hi again", visit 25 "roommates" (as designed).
                "Visit {visit}. Hi again.",
                "Visit {visit}. The feed missed you. Probably.",
                "Visit {visit}. Same app, new you? Let's see.",
                "Visit {visit}. I saved your seat. You could also not sit.",
                "Visit {visit}. We're basically roommates now.",
                "Visit {visit}. Oh hey. Didn't expect you. (I did.)",
                "Visit {visit}. Back already? Bold.",
            ],
            .notice: [
                "{elapsed} in. Still fun? Honest answers only.",
                "{elapsed} in {app}. Is the algorithm winning?",
                "{elapsed}. Your thumb would like a word.",
                "{elapsed} in. Plot twist: you could leave.",
                "{elapsed} down. The feed is endless. Your evening isn't.",
                "{elapsed}. Just checking in, like a nosy friend.",
            ],
            .nudge: [
                "{elapsed}. Your thumb has travelled about {distance}. Impressive thumb.",
                "That's {landmark} of scrolling. Sightseeing done?",
                "{elapsed} in {app}. The reels will survive without you.",
                "{elapsed}. If this were a movie, we'd be in the slow middle.",
                "About {distance} of thumb travel. Personal best? Let's not.",
                "{elapsed}. Your phone is warm. Your tea is probably cold.",
            ],
            .shield: [
                "Welcome back. We're basically roommates now.",
                "Oh hey. Didn't expect you. (I did.)",
                "Same app, same feed, new you? Let's see.",
                "I saved your seat. You could also not sit.",
                "Back so soon? The reels missed you less.",
                "Limit's done. The feed will keep. Promise.",
            ],
        ],
        .blunt: [
            .arrive: [
                "Visit {visit}. You know the drill.",
                "Visit {visit}. What are you here for?",
                "Visit {visit}. In and out.",
                "Visit {visit} today. Make it quick.",
                "Visit {visit}. Name one thing you need in here.",
                "Visit {visit}. Clock's running.",
            ],
            .notice: [
                "{elapsed}. Put it down.",
                "{elapsed} in {app}. Done yet?",
                "{elapsed}. You've probably seen the good bits.",
                "{elapsed}. Close it.",
                "{elapsed} in. Nothing new is coming.",
                "{elapsed}. Decide: stay or go.",
            ],
            .nudge: [
                "{elapsed}. About {distance} of scrolling. Stop.",
                "{elapsed} in {app}. This is the spiral.",
                "{elapsed}. Phone down. Now.",
                "{elapsed}. You've seen this already.",
                "That's {landmark}. Plenty.",
                "{elapsed}. Leave while it's easy.",
            ],
            .shield: [
                "Limit hit. Close it.",
                "That's your limit. You set it.",
                "Done for today.",
                "Limit reached. Go do the other thing.",
                "No more today. Close the app.",
                "You're past your limit. Time to go.",
            ],
        ],
    ]

    /// Lines shown during the control week (nudges off): plain, Screen-Time-like.
    static let plainShieldTitle = "Time Limit"

    static func plainShieldSubtitle(limitMinutes: Int) -> String {
        "You've reached your \(limitMinutes)-minute limit on this app."
    }

    /// Celebrations for walk-aways (Today screen / widget). No numbers to get wrong.
    static let walkAwayLines = [
        "Each one counts. Literally.",
        "Leaving is the win.",
        "You closed it. That's the whole trick.",
    ]

    /// Picks a line deterministically from `seed` (usually the visit count), so the
    /// copy changes on every return but the same visit always reads the same.
    static func line(voice: Voice, level: NudgeLevel, seed: Int, context: Context) -> String {
        let options = lines[voice]?[level] ?? []
        guard !options.isEmpty else { return "" }
        let index = ((seed % options.count) + options.count) % options.count
        return fill(options[index], context)
    }

    static func fill(_ template: String, _ c: Context) -> String {
        var text = template
            .replacingOccurrences(of: "{visit}", with: "\(c.visit)")
            .replacingOccurrences(of: "{app}", with: c.app)
            .replacingOccurrences(of: "{distance}", with: "\(Odometer.format(metres: c.metres)) (est.)")
            .replacingOccurrences(of: "{landmark}", with: Odometer.phrase(metres: c.metres))
        let elapsed = Format.elapsed(seconds: c.elapsedSeconds)
        // Capitalise when the line starts with the elapsed time.
        if text.hasPrefix("{elapsed}") {
            text = text.replacingOccurrences(of: "{elapsed}", with: elapsed.prefix(1).uppercased() + elapsed.dropFirst())
        }
        return text.replacingOccurrences(of: "{elapsed}", with: elapsed)
    }
}
