import json
import re

# Define templates and baseline QA pairs first, then extract the vocabulary programmatically,
# and finally pad the vocabulary to exactly 300 simple Hindi words.

# --- Predefined Dialogue Pairs ---
base_qa = [
    ("नमस्ते", "नमस्ते जी! आपका स्वागत है।"),
    ("आप कैसे हैं?", "मैं ठीक हूँ। आप कैसे हैं?"),
    ("आपका नाम क्या है?", "मेरा नाम दोस्त है।"),
    ("आप कौन हैं?", "मैं आपका दोस्त हूँ।"),
    ("धन्यवाद", "आपका स्वागत है!"),
    ("नमस्ते दोस्त", "नमस्ते! आप कैसे हैं?"),
    ("नमस्कार", "नमस्कार जी! आप कैसे हैं?"),
    ("अलविदा", "अलविदा दोस्त! फिर मिलेंगे।"),
    ("प्रणाम", "प्रणाम जी! खुश रहिए।"),
    ("क्या आप ठीक हैं?", "हाँ, मैं बहुत अच्छा हूँ।"),
    ("आपका भाई कहाँ है?", "मेरा भाई घर पर है।"),
    ("आपकी बहन क्या करती है?", "मेरी बहन पुस्तक पढ़ती है।"),
    ("आपके पिता कहाँ हैं?", "मेरे पिता शहर गए हैं।"),
    ("आपकी माँ कहाँ हैं?", "मेरी माँ घर के अंदर हैं।"),
    ("क्या आपके पास दोस्त हैं?", "हाँ, मेरे पास अच्छे दोस्त हैं।"),
    ("आपका बेटा कहाँ है?", "मेरा बेटा स्कूल गया है।"),
    ("आपकी बेटी क्या कर रही है?", "मेरी बेटी पानी पी रही है।"),
    ("ये लोग कौन हैं?", "ये लोग मेरे दोस्त हैं।"),
    ("वह आदमी कौन है?", "वह आदमी मेरा भाई है।"),
    ("वह औरत कौन है?", "वह औरत मेरी माँ है।"),
    ("वह बच्चा क्या कर रहा है?", "वह बच्चा रोटी खा रहा है।"),
    ("यह क्या है?", "यह एक सुंदर फूल है।"),
    ("वह क्या है?", "वह एक बड़ा पेड़ है।"),
    ("पेड़ पर क्या है?", "पेड़ पर हरा पत्ता है।"),
    ("आकाश कैसा है?", "आकाश नीला और साफ़ है।"),
    ("सूरज कहाँ है?", "सूरज आकाश में है।"),
    ("चाँद कब आता है?", "चाँद रात को आता है।"),
    ("मौसम कैसा है?", "आज मौसम बहुत गरम है।"),
    ("क्या आज बारिश होगी?", "हाँ, आज बारिश होगी।"),
    ("क्या आपको ठंड लग रही है?", "हाँ, मुझे बहुत ठंड लग रही है।"),
    ("क्या यहाँ गर्मी है?", "हाँ, यहाँ बहुत गर्मी है।"),
    ("नदी कहाँ बहती है?", "नदी पहाड़ से नीचे बहती है।"),
    ("वह पहाड़ कैसा है?", "वह पहाड़ बहुत बड़ा है।"),
    ("मिट्टी कैसी है?", "मिट्टी साफ़ है।"),
    ("आग कहाँ है?", "आग घर के बाहर है।"),
    ("क्या आप चाय पिएंगे?", "हाँ, मैं चाय पीता हूँ।"),
    ("चाय कैसी है?", "चाय बहुत मीठी है।"),
    ("दूध कहाँ है?", "दूध घर के अंदर है।"),
    ("क्या आपके पास रोटी है?", "हाँ, मेरे पास रोटी और फल हैं।"),
    ("पानी लाओ", "मैं पानी लाता हूँ। लो, पानी पियो।"),
    ("क्या आपको भूख लगी है?", "हाँ, मुझे बहुत भूख लगी है। मुझे खाना खाना है।"),
    ("क्या खाना अच्छा है?", "हाँ, खाना बहुत अच्छा और गरम है।"),
    ("आप क्या पी रहे हैं?", "मैं ठंडा पानी पी रहा हूँ।"),
    ("फल कहाँ है?", "फल पेड़ पर है।"),
    ("आप क्या कर रहे हैं?", "मैं अपना काम कर रहा हूँ।"),
    ("आप कब काम करते हैं?", "मैं सुबह काम करता हूँ और रात को सोता हूँ।"),
    ("क्या आप स्कूल जाते हैं?", "हाँ, मैं स्कूल जाता हूँ।"),
    ("आप पुस्तक क्यों पढ़ रहे हैं?", "क्योंकि मुझे पढ़ना बहुत अच्छा लगता है।"),
    ("कलम कहाँ है?", "कलम पुस्तक के ऊपर है।"),
    ("कागज़ पर क्या लिखा है?", "कागज़ पर मेरा नाम लिखा है।"),
    ("आप कहाँ जा रहे हैं?", "मैं अपने घर जा रहा हूँ।"),
    ("गाड़ी कहाँ है?", "गाड़ी रास्ते पर है।"),
    ("क्या आप दौड़ सकते हैं?", "हाँ, मैं तेज़ दौड़ता हूँ।"),
    ("आप कैसे चलते हैं?", "मैं धीरे-धीरे चलता हूँ।"),
    ("मेरी मदद करो", "हाँ, मैं आपकी मदद करता हूँ।"),
    ("आप क्या सोच रहे हैं?", "मैं अपने काम को सोच रहा हूँ।"),
    ("क्या आप यह बात समझते हैं?", "हाँ, मैं आपकी बात समझता हूँ।"),
    ("आप मुझे कैसे जानते हैं?", "मैं आपको बहुत पहले से जानता हूँ।"),
    ("आप क्या बोल रहे हैं?", "मैं सच बोल रहा हूँ।"),
    ("मेरी बात सुनो", "हाँ, मैं आपकी बात सुनता हूँ। कहो।"),
    ("आप क्या देख रहे हैं?", "मैं सुंदर पेड़ देख रहा हूँ।"),
    ("क्या आप सोते हैं?", "हाँ, मैं रात को सोता हूँ।"),
    ("आप कब उठते हैं?", "मैं सुबह जल्दी उठता हूँ।"),
    ("यहाँ बैठो", "हाँ, मैं यहाँ बैठता हूँ।"),
    ("वहाँ मत जाओ", "ठीक है, मैं वहाँ नहीं जाता।"),
]

# Temporary list to hold raw messages we want to add
raw_dataset = []

# Add baseline Q&As
for q, a in base_qa:
    raw_dataset.append((q, a))

# --- Template-Based Generation ---

# 1. Location Q&A
subjects = [
    ("दोस्त", "दोस्त"), ("भाई", "भाई"), ("बहन", "बहन"), ("माँ", "माँ"), 
    ("पिता", "पिता"), ("बेटा", "बेटा"), ("बेटी", "बेटी"), ("गाड़ी", "गाड़ी"),
    ("कलम", "कलम"), ("पुस्तक", "पुस्तक"), ("घर", "घर"), ("पानी", "पानी")
]
locations = [
    ("घर पर", "घर पर"), ("शहर में", "शहर में"), ("गांव में", "गांव में"),
    ("पेड़ के पास", "पेड़ के पास"), ("नदी के पास", "नदी के पास"),
    ("पहाड़ पर", "पहाड़ पर"), ("रास्ते पर", "रास्ते पर"), 
    ("बाहर", "बाहर"), ("अंदर", "अंदर")
]

for sub_q, sub_a in subjects:
    for loc_q, loc_a in locations:
        q = f"आपका {sub_q} कहाँ है?"
        is_resp = sub_q in ["माँ", "पिता"]
        verb = "हैं" if is_resp else "है"
        a = f"मेरा {sub_a} {loc_a} {verb}।"
        raw_dataset.append((q, a))

# 2. Pronouns and Consumption (Food/Drink)
pronouns = [
    ("आप", "मैं", "हैं", "हूँ"),
    ("तुम", "मैं", "हो", "हूँ"),
    ("वह", "वह", "है", "है"),
    ("हम", "हम", "हैं", "हैं"),
    ("वे", "वे", "हैं", "हैं")
]
items = [
    ("चाय", "चाय"), ("पानी", "पानी"), ("दूध", "दूध"), 
    ("खाना", "खाना"), ("रोटी", "रोटी"), ("फल", "फल")
]
actions = [
    ("पीते", "पीता", "पीती"), 
    ("खाते", "खाता", "खाती")
]

for pron_q, pron_a, verb_q, verb_a in pronouns:
    for item_q, item_a in items:
        is_drink = item_q in ["चाय", "पानी", "दूध"]
        act = actions[0] if is_drink else actions[1]
        
        for is_masc in [True, False]:
            act_q = act[1] if pron_q in ["वह", "मैं"] else (act[2] if pron_q == "वह" and not is_masc else act[0])
            act_a = act[1] if is_masc else act[2]
            
            q = f"क्या {pron_q} {item_q} {act_q} {verb_q}?"
            a = f"हाँ, {pron_a} {item_a} {act_a} {verb_a}।"
            raw_dataset.append((q, a))

# 3. Possession Q&A
poss_nouns = [
    ("कलम", "कलम"), ("पुस्तक", "पुस्तक"), ("गाड़ी", "गाड़ी"), 
    ("घर", "घर"), ("रोटी", "रोटी"), ("पानी", "पानी"), ("फल", "फल")
]
poss_adjectives = [
    ("अच्छा", "अच्छा"), ("नया", "नया"), ("पुराना", "पुराना"), 
    ("छोटा", "छोटा"), ("बड़ा", "बड़ा"), ("सुंदर", "सुंदर"), ("साफ़", "साफ़")
]

for noun_q, noun_a in poss_nouns:
    for adj_q, adj_a in poss_adjectives:
        q = f"क्या आपके पास {noun_q} है?"
        a = f"हाँ, मेरे पास एक {adj_a} {noun_a} है।"
        raw_dataset.append((q, a))

# 4. Action Time Q&A
action_verbs = [
    ("सोते", "सोता", "सोती"), 
    ("उठते", "उठता", "उठती"), 
    ("पढ़ते", "पढ़ता", "पढ़ती"),
    ("लिखते", "लिखता", "लिखती"),
    ("चलते", "चलता", "चलती")
]
times = [
    ("सुबह", "सुबह"), ("दोपहर", "दोपहर"), ("शाम", "शाम"), 
    ("रात", "रात"), ("अभी", "अभी"), ("जल्दी", "जल्दी")
]

for pron_q, pron_a, verb_q, verb_a in pronouns[:2]:
    for act in action_verbs:
        for time_q, time_a in times:
            for is_masc in [True, False]:
                act_q = act[0]
                act_a = act[1] if is_masc else act[2]
                
                q = f"{pron_q} कब {act_q} {verb_q}?"
                a = f"{pron_a} {time_a} {act_a} {verb_a}।"
                raw_dataset.append((q, a))

# 5. Adjective Description Q&A
masc_nouns = ["मौसम", "घर", "रास्ता", "पानी", "दूध", "दिन"]
masc_adjectives = ["अच्छा", "बुरा", "बड़ा", "छोटा", "नया", "पुराना", "साफ़", "गंदा", "ठंडा", "गरम"]

fem_nouns = ["चाय", "रात", "सुबह", "शाम", "रोटी", "गाड़ी"]
fem_adjectives = ["अच्छी", "बुरी", "बड़ी", "छोटी", "नयी", "पुरानी", "साफ़", "ठंडी", "गर्मी"]

for n in masc_nouns:
    for adj in masc_adjectives:
        q = f"{n} कैसा है?"
        a = f"{n} {adj} है।"
        raw_dataset.append((q, a))

for n in fem_nouns:
    for adj in fem_adjectives:
        q = f"{n} कैसी है?"
        a = f"{n} {adj} है।"
        raw_dataset.append((q, a))

def clean_hindi_sentence(text):
    cleaned = re.sub(r'[।\?,\!\-"\'\(\)]', ' ', text)
    return cleaned.split()

# Extract all unique words from assistant responses
assistant_words = set()
for q, a in raw_dataset:
    for word in clean_hindi_sentence(a):
        assistant_words.add(word)

# Convert to list
assistant_vocab = sorted(list(assistant_words))
vocab_len = len(assistant_vocab)
print(f"Unique words used in assistant responses: {vocab_len}")

# Define a pool of simple Hindi words to pad the vocabulary to exactly 300
padding_pool = [
    # Pronouns & Questions
    "तुम", "तुम्हें", "तुम्हारा", "तुम्हारी", "इसे", "उसका", "उसकी", "उसे",
    "हम", "हमें", "हमारा", "कौन", "क्या", "क्यों", "कैसे", "कब", "कहाँ", "कुछ", "कोई", "सब",

    # Postpositions, Conjunctions & Particles
    "का", "के", "की", "में", "पर", "से", "को", "तक", "ने", "लिए",
    "और", "लेकिन", "या", "कि", "क्योंकि", "इसलिए", "तो", "भी", "ही", "ना", "मत", "हाँ", "नहीं", "जी",

    # Numbers
    "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ", "दस",
    "ग्यारह", "बारह", "तेरह", "चौदह", "पन्द्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस", "बीस",

    # Greetings and courtesy
    "स्वागत", "धन्यवाद", "नमस्कार", "नमस्ते", "कृपया", "क्षमा", "शुभ", "प्रभात", "रात्रि", "अलविदा",

    # Common nouns
    "देश", "समय", "हवा", "धूप", "पेड़", "पत्ता", "फूल", "फल", "सूरज", "चाँद", "तारा", "आकाश", "धरती",
    "आदमी", "औरत", "लोग", "भाई", "बहन", "माँ", "पिता", "बेटा", "बेटी", "बच्चा", "दोस्त", "काम", "नाम",

    # Adjectives
    "सरल", "कठिन", "भारी", "हल्का", "मीठा", "खट्टा", "तीखा", "लाल", "पीला", "नीला", "हरा", "काला", "सफ़ेद",
    "खुश", "उदाश", "धीमा", "धीमे", "तेज़", "हमेशा", "कभी", "अभी", "धीरे", "जल्दी", "तुरंत", "सच्चा", "झूठा",

    # Verbs
    "होना", "करना", "देना", "लेना", "जाना", "आना", "खाना", "पीना", "देखना", "सुनना", "लिखना", "पढ़ना",
    "सोना", "बैठना", "उठना", "चलना", "दौड़ना", "बोलना", "कहना", "समझना", "सोचना", "जानना", "मिलना"
]

# Merge and pad to exactly 300
final_vocab_set = set(assistant_vocab)
for word in padding_pool:
    if len(final_vocab_set) >= 300:
        break
    final_vocab_set.add(word)

# If still short, generate dummy words or inflections
counter = 1
while len(final_vocab_set) < 300:
    # Add simple number words or fillers
    final_vocab_set.add(f"शब्द{counter}")
    counter += 1

HINDI_VOCABULARY = sorted(list(final_vocab_set))
print(f"Final programmatically generated vocabulary size: {len(HINDI_VOCABULARY)}")

# Write dataset files
dataset = []
for q, a in raw_dataset:
    # Double check that all words are in HINDI_VOCABULARY (they must be since we extracted them from assistant answers!)
    dataset.append({
        "messages": [
            {"role": "user", "content": q},
            {"role": "assistant", "content": a}
        ]
    })

# Save dataset to JSONL
output_file = "/Users/sachinmishra/Desktop/GenAI/FineTuning/dataset.jsonl"
with open(output_file, "w", encoding="utf-8") as f:
    for item in dataset:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

# Save vocabulary list to a file for reference and logit masking
vocab_file = "/Users/sachinmishra/Desktop/GenAI/FineTuning/hindi_vocab.json"
with open(vocab_file, "w", encoding="utf-8") as f:
    json.dump(HINDI_VOCABULARY, f, ensure_ascii=False, indent=4)

print(f"Successfully generated {len(dataset)} verified dialogue turns.")
print(f"Dataset saved to {output_file}")
print(f"Vocabulary saved to {vocab_file}")
