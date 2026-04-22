import { useMemo } from "react";

const CATEGORY_ORDER = [
  "analgesics",
  "antibiotics",
  "antimalarials",
  "antihistamines",
  "antipyretics",
  "antifungals",
  "antivirals",
  "gastrointestinal",
  "respiratory",
  "supplements",
  "vaccines",
  "hormonal",
  "cardiovascular",
  "other",
];

export default function DrugAvailabilityPanel({ drugs = [], title = "Available Drugs" }) {
  const grouped = useMemo(() => {
    const groups = new Map();
    drugs.forEach((drug) => {
      const key = drug.category || "other";
      const label = drug.category_label || "Other";
      if (!groups.has(key)) {
        groups.set(key, { key, label, items: [] });
      }
      groups.get(key).items.push(drug);
    });

    return Array.from(groups.values()).sort((a, b) => {
      const aIndex = CATEGORY_ORDER.indexOf(a.key);
      const bIndex = CATEGORY_ORDER.indexOf(b.key);
      return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex);
    });
  }, [drugs]);

  if (!drugs.length) return null;

  return (
    <div className="available-drugs-panel">
      <h5>{title}</h5>
      {grouped.map((group) => (
        <div key={group.key} className="drug-category-group">
          <h6>{group.label}</h6>
          <ul>
            {group.items.map((drug) => (
              <li key={`${drug.id}-${drug.amount}`}>
                <strong>{drug.drug_name}</strong> - {drug.label}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
