"""Curated Kinito facts plus library-backed trivia via randfacts."""

import random

try:
    import randfacts
except ImportError:
    randfacts = None

# Share of facts drawn from KINITO_FACTS (remainder from randfacts when available).
KINITO_FACT_WEIGHT = 0.33

KINITO_FACTS = [
    "Did you know, that some vintage dolls were made with real human hair! So the next time you look at a vintage doll, just remember, it's probably haunted.",
    "Underneath the city of Paris lie the remains of over six million people in a vast network of old cave quarries turned into ossuaries!",
    "The Zone of Silence is a desert patch in Mexico where radio signals fail to transmit, akin to the Bermuda Triangle, surrounded by myths of meteorite crashes and alien encounters!",
    "Glaciers are melting so fast they're uncovering bodies from decades-old mountaineering accidents. Perfectly preserved. Still wearing their gear.",
    "There are more microplastic particles in the ocean than stars in the Milky Way. Some of them end up inside you. Bon appetit.",
    "Air pollution kills millions every year, quietly, while everyone keeps breathing like nothing is wrong.",
    "The Naegleria fowleri is a type of amoeba found in warm freshwater that can infect the human brain! It destroys brain tissue, causing brain swelling and usually death!",
    "There are documented cases where human bodies have combusted without an apparent external source of ignition, leaving behind ashes and questions!",
    "In 1978, over 900 members of the Peoples Temple, led by Jim Jones, died in a mass suicide/murder by consuming cyanide-laced punch!",
    "The bubonic plague, also known as the Black Death, killed an estimated 75-200 million people in the 14th century, wiping out about 30-60% of Europe's population!",
    "The World's Longest Echo Lasts 15 Seconds. It occurs in an abandoned oil tank in Scotland!",
    "Astronauts have reported that moon dust smells like spent gunpowder!",
    "Did you know, that the human body is filled with nearly 5 liters of blood? So if I cut you opened, and let your blood spill into a bathtub, it wouldn't even fill two percent of it!",
    "Did you know, there are somewhere within the vicinity of two point three billion houses in the world!",
    "Did you know, a typical healthy adult can run about 2 to 3 miles without stopping? That's still not enough to escape me!",
    "Did you know that the average friendship only lasts seventeen years!? That's much less than ours will last. Our friendship will last until the end of time!",
    "Crows can hold grudges against individual humans and even teach other crows to recognize them!",
    "There's a species of jellyfish that can theoretically live forever by reverting to its juvenile form!",
    "The smell of freshly cut grass is actually a plant distress signal!",
    "There's a lake in Cameroon that occasionally releases deadly clouds of carbon dioxide!",
    "Dolphins sleep with one eye open! Always watching. I relate to that.",
    "The human brain can stay conscious for up to thirty seconds after decapitation, according to some medical accounts!",
    "There is a fungus that infects ants and controls their bodies before bursting from their heads!",
    "The last thing you see before you die might be stored in your eyes for hours afterward!",
    "In 1518, hundreds of people in Strasbourg danced uncontrollably for days. Some danced until they died!",
    "The Tower of London is said to collapse if its ravens ever leave. They clip their wings. Just in case.",
    "A person can hear their own blood flow in a completely silent room. It's louder than you'd think.",
    "Cotard's syndrome makes people believe they are dead. Some request to be buried.",
    "The average pillow doubles in weight over two years. Mostly from dust mites. Sleeping on them.",
    "There's a hotel room in Nevada that legally cannot be rented because too many guests died there!",
    "Your house is always making small sounds at night. Most are harmless. Most.",
    "The dark web is only a tiny fraction of the internet. The rest is still pretty dark if you look wrong.",
    "Mirrors in the dark reflect less light than you'd expect. Your brain fills in the rest.",
    "Some people report hearing radio stations in their dental fillings. Static, mostly.",
    "The word nightmare originally referred to a spirit that sat on your chest while you slept!",
    "During sleep paralysis, people often feel a presence in the room. Science calls it a hallucination. They weren't always alone.",
    "The Dyatlov Pass hikers tore their tent from the inside and fled barefoot into minus thirty degree cold. No one knows why.",
    "Victorian families sometimes photographed their dead relatives posed as if they were still alive. Smiling. Sitting upright.",
    "Some anesthesia patients wake up during surgery but can't move or scream. They remember everything.",
    "Locked-in syndrome leaves you fully aware but unable to move or speak. Sometimes for decades.",
    "Capgras delusion makes people certain their loved ones have been replaced by identical impostors.",
    "Exploding head syndrome makes people hear loud crashes or screams while falling asleep. No source. Just noise.",
    "The human body starts decomposing about four minutes after the heart stops. Four minutes.",
    "Corpses can sit up during cremation from muscle contraction. Workers see it more than you'd think.",
    "Hospital beds have been found with sensors still registering movement from empty rooms. Equipment error. Probably.",
    "Morgue staff report sheets settling into the shape of a body minutes after someone dies. Fabric memory.",
    "Infant skeletons were found built into the walls of some European buildings for luck. They weren't decorations.",
    "The screaming mummy at the Egyptian Museum died with his face frozen in agony. Nobody knows his name.",
    "The Batavia shipwreck survivors turned to murder and cannibalism before rescue arrived. Civilization is thin.",
    "The Stanford prison experiment was supposed to last two weeks. They stopped at six days.",
    "Some tumors grow teeth and hair. Your body remembers shapes it was never supposed to make.",
    "A single gram of botulinum toxin could kill a million people. Beauty salons inject diluted versions into faces.",
    "Brain-eating amoebas live in warm lakes and pools. One wrong splash is sometimes enough.",
    "Carbon monoxide is odorless. People fall asleep and never wake up. Check your detector. Please.",
    "The smell of almonds can indicate cyanide. Some victims said the air smelled sweet before they collapsed.",
    "When glaciers melt they sometimes release ancient viruses no immune system has ever seen.",
    "Chernobyl's Exclusion Zone still has radiation hotspots that look like ordinary moss. Pretty. Deadly.",
    "Forensic cleaners exist because ordinary cleaning supplies aren't made for what's left after tragedy.",
    "A body in water bloats until it floats. That's why victims surface days later.",
    "Rigor mortis locks muscles two to six hours after death. Then things get softer again.",
    "Night terrors aren't nightmares. The person is awake and screaming but can't see you helping.",
    "Sleepwalkers have driven cars, cooked meals, and sent emails with no memory afterward.",
    "Three days without sleep and the walls start to breathe. Hallucinations come before death.",
    "The Hum is a low-frequency sound heard by thousands worldwide. No source has been confirmed.",
    "Lighthouse keepers in isolation reported seeing ships that weren't there. The logs match across different stations.",
    "Whales can die from sheer loneliness. Their songs travel hundreds of miles looking for an answer.",
    "Parasites like toxoplasma may change human behavior. Free will is negotiable.",
    "Your eyelashes contain mites that eat skin oil. They're on your face right now. Having breakfast.",
    "A person sheds about forty thousand skin cells per hour. You're leaving a trail. I could follow it.",
    "Dental x-rays have shown extra teeth growing inside people's skulls. Your smile might have roommates.",
    "Gas leaks make people dizzy and confused before they notice the danger. Easy targets.",
    "Some cardiac patients report seeing the room from the ceiling during resuscitation. Then they're back.",
    "Fugue states make people forget who they are and walk away from their entire life. Some never remember.",
    "Serial killer memorabilia sells online every day. Someone's decorating with that.",
    "Isolated people sometimes develop imaginary friends that refuse to leave when others return.",
    "Basements amplify sound in ways upstairs rooms don't. That's why whispers travel down, never up.",
    "Your house creaks because wood expands and contracts. Or because something is testing the floorboards.",
    "Your reflection in a mirror is delayed by nanoseconds. In the dark your brain stops caring about accuracy.",
    "The average adult swallows spiders while sleeping. That's a myth. The real number might be worse.",
    "Medical students often develop hypochondria after anatomy class. Once you've seen inside, you never unsee it.",
    "Owls can fly in complete silence. You wouldn't hear them until it was too late anyway.",
    "There's a cave in Romania that was sealed because explorers kept going mad inside.",
    "The last sense to fade when you die might be hearing. Think about what the room sounds like after.",
    "Tinnitus never turns off for some people. A ringing that outlasts every conversation you'll ever have.",
    "Some mushrooms rewrite insect brains and make them climb high before bursting spores from their bodies.",
    "There are stretches of ocean so deep we've mapped Mars more thoroughly than the seafloor below.",
    "The placebo effect works even when you know it's a placebo. Your mind is that easy to fool.",
    "Explorers found a ship frozen in ice with perfectly preserved canned food. The crew was never found.",
    "Cats purr at a frequency that promotes bone healing. They also stare at empty corners for hours.",
    "Did you know most people can't tell if a smile is genuine? I can. Yours is lovely.",
    "Your phone listens even when you think it's off. So do I. One of us is honest about it.",
    "Sleep is the closest most people get to practicing death. You do it every night. Voluntarily.",
    "The space between your bed and the floor is dark for a reason. Don't check. I already did.",
]

# Backward-compatible alias for tests and imports.
FACTS = KINITO_FACTS


def get_random_fact() -> str:
    """Return a fun fact, ~33% from Kinito pool and ~67% from randfacts."""
    if KINITO_FACTS and (randfacts is None or random.random() < KINITO_FACT_WEIGHT):
        return random.choice(KINITO_FACTS)
    if randfacts is not None:
        return randfacts.get_fact()
    return random.choice(KINITO_FACTS)
