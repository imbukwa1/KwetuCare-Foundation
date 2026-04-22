export default function PrescriptionEditor({
  prescriptions,
  availableDrugs,
  updatePrescriptionField,
  addPrescription,
  removePrescription,
}) {
  const onDrugChange = (index, value) => {
    const selected = availableDrugs.find((item) => String(item.id) === String(value));
    if (!selected) {
      updatePrescriptionField(index, "inventoryId", "");
      updatePrescriptionField(index, "drugName", "");
      updatePrescriptionField(index, "dosage", "");
      return;
    }
    updatePrescriptionField(index, "inventoryId", String(selected.id));
    updatePrescriptionField(index, "drugName", selected.drug_name);
    updatePrescriptionField(index, "dosage", selected.amount);
  };

  return (
    <>
      {prescriptions.map((prescription, index) => (
        <div className="prescription-row" key={index}>
          <select
            value={prescription.inventoryId || ""}
            onChange={(event) => onDrugChange(index, event.target.value)}
          >
            <option value="">Select stocked drug</option>
            {availableDrugs.map((drug) => (
              <option key={`${drug.id}-${drug.amount}`} value={drug.id}>
                {drug.drug_name} - {drug.amount} ({drug.stock_quantity} available)
              </option>
            ))}
          </select>
          <input value={prescription.dosage} readOnly placeholder="Dosage/Strength" />
          <input
            type="number"
            min="1"
            value={prescription.quantity}
            onChange={(event) => updatePrescriptionField(index, "quantity", event.target.value)}
            placeholder="Quantity"
          />
          <select
            value={prescription.frequency}
            onChange={(event) => updatePrescriptionField(index, "frequency", event.target.value)}
          >
            <option value="">Frequency</option>
            <option value="once daily">Once daily</option>
            <option value="twice daily">Twice daily</option>
            <option value="three times daily">Three times daily</option>
            <option value="as needed">As needed</option>
          </select>
          {prescriptions.length > 1 && (
            <button type="button" className="btn-remove" onClick={() => removePrescription(index)}>
              Remove
            </button>
          )}
        </div>
      ))}
      <button type="button" className="btn-muted" onClick={addPrescription} disabled={!availableDrugs.length}>
        + Add Drug
      </button>
    </>
  );
}
