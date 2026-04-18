/**
 * IFCT 2017 Seed Script
 *
 * Reads the @ifct2017/compositions CSV, transforms each food into
 * a JSON object matching the v2_ingredients schema, runs data quality
 * checks, and writes ifct_seed_data.json.
 *
 * Usage:  cd ifct-test && node seed_ifct.js
 * Output: ifct-test/ifct_seed_data.json
 */

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------------
// 1. Load and parse CSV
// ---------------------------------------------------------------------------

const csvPath = require("@ifct2017/compositions").csv();
const raw = fs.readFileSync(csvPath, "utf8");
const lines = raw.split("\n");

// Parse header → field codes
const headerFields = lines[0]
  .split(",")
  .map((f) => f.replace(/^"|"$/g, "").trim());
const fieldCodes = headerFields.map((h) => {
  const parts = h.split(";");
  return parts.length > 1 ? parts[1].trim() : parts[0].trim();
});

// Build code→index map
const idx = {};
fieldCodes.forEach((code, i) => {
  idx[code] = i;
});

// Simple CSV row parser (handles quoted fields)
function parseRow(line) {
  const fields = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    if (line[i] === '"') inQuotes = !inQuotes;
    else if (line[i] === "," && !inQuotes) {
      fields.push(current.trim());
      current = "";
    } else current += line[i];
  }
  fields.push(current.trim());
  return fields;
}

// ---------------------------------------------------------------------------
// 2. Regional name parsing
// ---------------------------------------------------------------------------

const LANG_PREFIXES = {
  "A.": "assamese",
  "B.": "bengali",
  "E.": "english",
  "G.": "gujarati",
  "H.": "hindi",
  "Kan.": "kannada",
  "Kash.": "kashmiri",
  "Kh.": "khasi",
  "Kon.": "konkani",
  "Mal.": "malayalam",
  "M.": "manipuri",
  "Mar.": "marathi",
  "N.": "nepali",
  "O.": "odia",
  "P.": "punjabi",
  "S.": "sanskrit",
  "Tam.": "tamil",
  "Tel.": "telugu",
  "U.": "urdu",
};

// Sort prefixes longest-first to avoid "M." matching before "Mar." or "Mal."
const SORTED_PREFIXES = Object.keys(LANG_PREFIXES).sort(
  (a, b) => b.length - a.length
);

function parseRegionalNames(langStr) {
  const names = {};
  const aliases = [];

  if (!langStr) return { names, aliases };

  // Split on semicolons
  const parts = langStr.split(";").map((s) => s.trim()).filter(Boolean);

  for (const part of parts) {
    let matched = false;
    for (const prefix of SORTED_PREFIXES) {
      if (part.startsWith(prefix)) {
        const value = part.substring(prefix.length).trim();
        if (value) {
          const lang = LANG_PREFIXES[prefix];
          // A language may appear multiple times with different names
          if (names[lang]) {
            names[lang] += ", " + value;
          } else {
            names[lang] = value;
          }
          // Add each comma-separated name as an alias
          value.split(",").forEach((v) => {
            const trimmed = v.trim().toLowerCase();
            if (trimmed && !aliases.includes(trimmed)) aliases.push(trimmed);
          });
        }
        matched = true;
        break;
      }
    }
    // If no prefix matched, still add as alias
    if (!matched && part.trim()) {
      const trimmed = part.trim().toLowerCase();
      if (trimmed && !aliases.includes(trimmed)) aliases.push(trimmed);
    }
  }

  return { names, aliases };
}

// ---------------------------------------------------------------------------
// 3. Form inference (raw / cooked / unspecified)
// ---------------------------------------------------------------------------

const RAW_KEYWORDS = ["raw", "uncooked", "dry", "dried", "sun-dried", "dehusked"];
const COOKED_KEYWORDS = [
  "cooked", "boiled", "steamed", "fried", "roasted", "baked",
  "toasted", "grilled", "stewed", "braised", "poached",
  "pressure cooked", "pressure-cooked",
];

function inferForm(name) {
  const lower = name.toLowerCase();
  for (const kw of COOKED_KEYWORDS) {
    if (lower.includes(kw)) return "cooked";
  }
  for (const kw of RAW_KEYWORDS) {
    if (lower.includes(kw)) return "raw";
  }
  return "unspecified";
}

// ---------------------------------------------------------------------------
// 4. Helper: safe float parsing
// ---------------------------------------------------------------------------

function num(fields, fieldCode) {
  const i = idx[fieldCode];
  if (i === undefined) return null;
  const v = parseFloat(fields[i]);
  return isNaN(v) ? null : v;
}

// ---------------------------------------------------------------------------
// 5. Process all foods
// ---------------------------------------------------------------------------

const dataLines = lines
  .slice(1)
  .filter((l) => l.trim().length > 0);

console.log(`Processing ${dataLines.length} foods from IFCT CSV...`);

const foods = [];
const qualityStats = { clean: 0, suspect_macros: 0, energy_derived: 0, suspect_fat: 0 };
const formStats = { raw: 0, cooked: 0, unspecified: 0 };
const groupCounts = {};
const duplicateNames = {};

const COMMON_NAMES = [
  "ghee", "rice", "dal", "paneer", "chicken", "milk", "curd",
  "wheat", "egg", "fish", "oil", "butter", "potato", "onion",
];

for (const line of dataLines) {
  const f = parseRow(line);
  if (f.length < 30) continue; // skip malformed rows

  const code = f[idx.code];
  const name = f[idx.name];
  const scientificName = f[idx.scie] || null;
  const foodGroup = f[idx.grup];
  const regionCode = parseInt(f[idx.regn]) || null;
  const tagsRaw = f[idx.tags] || "";

  // Parse regional names
  const { names: regionalNames, aliases: searchAliases } = parseRegionalNames(f[idx.lang]);
  // Also add the primary name (lowercased) to aliases
  const primaryLower = name.toLowerCase();
  if (!searchAliases.includes(primaryLower)) searchAliases.unshift(primaryLower);

  // Diet tags
  const dietTags = tagsRaw.split(/\s+/).filter(Boolean);

  // Form
  const form = inferForm(name);
  formStats[form]++;

  // --- Macros ---
  const enerc_kj = num(f, "enerc") || 0;
  let kcal = enerc_kj / 4.184;
  const protein_g = num(f, "protcnt") || 0;
  const fat_g = num(f, "fatce") || 0;
  const carbs_g = num(f, "choavldf") || 0;
  const fiber_g = num(f, "fibtg") || 0;

  // --- Data quality checks ---
  let dataQuality = null;
  const calcKcal = protein_g * 4 + carbs_g * 4 + fat_g * 9;

  // Check 1: Zero-calorie trap (check first so we can backfill kcal)
  if (kcal === 0 && (protein_g > 0 || fat_g > 0 || carbs_g > 0)) {
    kcal = calcKcal;
    dataQuality = "energy_derived";
  }

  // Check 2: Macro-calorie consistency (only if kcal > 0 and not already flagged)
  if (!dataQuality && kcal > 0) {
    const deviation = Math.abs(calcKcal - kcal) / kcal;
    if (deviation > 0.15) {
      dataQuality = "suspect_macros";
    }
  }

  // Check 3: Fats and oils sanity (IFCT uses "Edible Oils and Fats")
  if (!dataQuality && (foodGroup === "Fats and Oils" || foodGroup === "Edible Oils and Fats")) {
    if (fat_g < 85 || fat_g > 100 || kcal < 750 || kcal > 950) {
      dataQuality = "suspect_fat";
    }
  }

  qualityStats[dataQuality || "clean"]++;

  // --- Fat breakdown ---
  const sat_fat_g = num(f, "fasat");
  const mufa_g = num(f, "fams");
  const pufa_g = num(f, "fapu");
  const trans_fat_g = num(f, "fatrn");
  const omega3_g = num(f, "facn3");
  const omega6_g = num(f, "facn6");
  const cholesterol_raw = num(f, "cholc");
  const cholesterol_mg = cholesterol_raw != null ? cholesterol_raw * 1000 : null;

  // --- Sugar / starch ---
  const sugar_g = num(f, "fsugar");
  const starch_g = num(f, "starch");

  // --- Minerals (stored in grams in CSV, convert to mg) ---
  const toMg = (v) => (v != null ? v * 1000 : null);
  const calcium_mg = toMg(num(f, "ca"));
  const iron_mg = toMg(num(f, "fe"));
  const magnesium_mg = toMg(num(f, "mg"));
  const zinc_mg = toMg(num(f, "zn"));
  const sodium_mg = toMg(num(f, "na"));
  const potassium_mg = toMg(num(f, "k"));
  const phosphorus_mg = toMg(num(f, "p"));

  // --- Vitamins ---
  const toMcg = (v) => (v != null ? v * 1e6 : null);
  const vit_a_mcg = toMcg(num(f, "vita"));
  const vit_c_mg = toMg(num(f, "vitc"));
  const vit_d_mcg = toMcg(num(f, "vitd"));
  const vit_b_mg = toMg(num(f, "vitb"));
  const vit_e_mg = toMg(num(f, "vite"));
  const folate_mcg = toMcg(num(f, "folsum"));

  // --- Other ---
  const water_g = num(f, "water");
  const ash_g = num(f, "ash");

  // --- Raw IFCT data (full row as object) ---
  const rawIfctData = {};
  fieldCodes.forEach((code, i) => {
    if (i < f.length) rawIfctData[code] = f[i];
  });

  // --- Nutrient errors (all _e fields) ---
  const nutrientErrors = {};
  fieldCodes.forEach((code, i) => {
    if (code.endsWith("_e") && i < f.length) {
      const val = parseFloat(f[i]);
      if (!isNaN(val) && val !== 0) nutrientErrors[code] = val;
    }
  });

  // --- Track food group counts ---
  groupCounts[foodGroup] = (groupCounts[foodGroup] || 0) + 1;

  // --- Track duplicate common names ---
  for (const cn of COMMON_NAMES) {
    if (name.toLowerCase().includes(cn)) {
      if (!duplicateNames[cn]) duplicateNames[cn] = [];
      duplicateNames[cn].push({ code, name });
    }
  }

  foods.push({
    code,
    name,
    scientific_name: scientificName,
    food_group: foodGroup,
    region_code: regionCode,
    regional_names: regionalNames,
    search_aliases: searchAliases,
    diet_tags: dietTags,
    form,
    kcal: Math.round(kcal * 100) / 100,
    enerc_kj,
    protein_g,
    fat_g,
    carbs_g,
    fiber_g,
    sugar_g,
    starch_g,
    sat_fat_g,
    mufa_g,
    pufa_g,
    trans_fat_g,
    omega3_g,
    omega6_g,
    cholesterol_mg,
    calcium_mg,
    iron_mg,
    magnesium_mg,
    zinc_mg,
    sodium_mg,
    potassium_mg,
    phosphorus_mg,
    vit_a_mcg,
    vit_c_mg,
    vit_d_mcg,
    vit_b_mg,
    vit_e_mg,
    folate_mcg,
    water_g,
    ash_g,
    raw_ifct_data: rawIfctData,
    nutrient_errors: Object.keys(nutrientErrors).length > 0 ? nutrientErrors : null,
    data_quality: dataQuality,
    data_source: "ifct_2017",
    confidence: "verified",
  });
}

// ---------------------------------------------------------------------------
// 6. Write output
// ---------------------------------------------------------------------------

const outputPath = path.join(__dirname, "ifct_seed_data.json");
fs.writeFileSync(outputPath, JSON.stringify(foods, null, 2));

// ---------------------------------------------------------------------------
// 7. Validation report
// ---------------------------------------------------------------------------

console.log("\n=== IFCT SEED REPORT ===\n");
console.log(`Total foods processed: ${foods.length}`);
console.log(`Output: ${outputPath}\n`);

console.log("--- Food Group Counts ---");
Object.entries(groupCounts)
  .sort((a, b) => b[1] - a[1])
  .forEach(([g, c]) => console.log(`  ${g}: ${c}`));

console.log("\n--- Data Quality Flags ---");
Object.entries(qualityStats).forEach(([flag, count]) =>
  console.log(`  ${flag}: ${count}`)
);

console.log("\n--- Form Inference ---");
Object.entries(formStats).forEach(([form, count]) =>
  console.log(`  ${form}: ${count}`)
);

// Cholesterol checks
const plantGroups = [
  "Cereals and Millets", "Green Leafy Vegetables", "Fruits",
  "Roots and Tubers", "Other Vegetables", "Pulses and Legumes",
  "Nuts and Oil Seeds", "Sugars", "Condiments and Spices",
];
const animalGroups = [
  "Milk and Milk Products", "Egg and Egg Products",
  "Fish and Shellfish", "Meat and Poultry",
];

console.log("\n--- Cholesterol Sanity ---");
let plantViolations = 0;
let animalViolations = 0;
for (const food of foods) {
  if (plantGroups.includes(food.food_group) && food.cholesterol_mg > 0) {
    plantViolations++;
    if (plantViolations <= 5) {
      console.log(`  WARN: Plant food with cholesterol: ${food.name} (${food.food_group}) = ${food.cholesterol_mg}mg`);
    }
  }
  if (animalGroups.includes(food.food_group) && (food.cholesterol_mg === 0 || food.cholesterol_mg === null)) {
    animalViolations++;
    if (animalViolations <= 5) {
      console.log(`  WARN: Animal food with zero cholesterol: ${food.name} (${food.food_group})`);
    }
  }
}
if (plantViolations > 5) console.log(`  ... and ${plantViolations - 5} more plant violations`);
if (animalViolations > 5) console.log(`  ... and ${animalViolations - 5} more animal violations`);
console.log(`  Plant foods with cholesterol > 0: ${plantViolations}`);
console.log(`  Animal foods with cholesterol = 0: ${animalViolations}`);

console.log("\n--- Duplicate Common Names (disambiguation needed) ---");
for (const [cn, entries] of Object.entries(duplicateNames)) {
  if (entries.length > 1) {
    console.log(`  '${cn}' -> ${entries.length} entries:`);
    entries.forEach((e) => console.log(`    ${e.code}: ${e.name}`));
  }
}

console.log("\n=== SEED COMPLETE ===");
