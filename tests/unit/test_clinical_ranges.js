import { classifyBiomarker } from './frontend/src/utils/clinicalRanges.js';

console.log('=== CLINICAL STATUS REFERENCE RANGE UNIT TESTS ===\n');

let passCount = 0;
let failCount = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`✅ PASS: ${message}`);
    passCount++;
  } else {
    console.log(`❌ FAIL: ${message}`);
    failCount++;
  }
}

// 1. User Target Patient Profile Verification
console.log('--- 1. User Target Patient Profile Verification ---');
const patientHbA1c = classifyBiomarker('HbA1c', 6.2);
assert(patientHbA1c.status === 'PREDIABETES', `HbA1c 6.2% -> Expected PREDIABETES, got ${patientHbA1c.status} (${patientHbA1c.label})`);

const patientFBG = classifyBiomarker('Fasting_Blood_Glucose', 118);
assert(patientFBG.status === 'PREDIABETES', `Fasting Glucose 118 mg/dL -> Expected PREDIABETES, got ${patientFBG.status} (${patientFBG.label})`);

const patientBP = classifyBiomarker('Blood_Pressure', 136, 86);
assert(patientBP.status === 'ELEVATED', `Blood Pressure 136/86 mmHg -> Expected ELEVATED, got ${patientBP.status} (${patientBP.label})`);

const patientTG = classifyBiomarker('Triglycerides', 186);
assert(patientTG.status === 'ELEVATED', `Triglycerides 186 mg/dL -> Expected ELEVATED, got ${patientTG.status} (${patientTG.label})`);

const patientALT = classifyBiomarker('ALT', 44);
assert(patientALT.status === 'NORMAL', `ALT 44 U/L -> Expected NORMAL, got ${patientALT.status} (${patientALT.label})`);

const patientBMI = classifyBiomarker('BMI', 27.7);
assert(patientBMI.status === 'OVERWEIGHT', `BMI 27.7 kg/m² -> Expected OVERWEIGHT, got ${patientBMI.status} (${patientBMI.label})`);


// 2. Boundary Value Tests (Task 6)
console.log('\n--- 2. Boundary Value Tests ---');

// HbA1c: 5.6, 5.7, 6.4, 6.5
assert(classifyBiomarker('HbA1c', 5.6).status === 'NORMAL', 'HbA1c 5.6% -> NORMAL');
assert(classifyBiomarker('HbA1c', 5.7).status === 'PREDIABETES', 'HbA1c 5.7% -> PREDIABETES');
assert(classifyBiomarker('HbA1c', 6.4).status === 'PREDIABETES', 'HbA1c 6.4% -> PREDIABETES');
assert(classifyBiomarker('HbA1c', 6.5).status === 'ELEVATED', 'HbA1c 6.5% -> ELEVATED');

// FBG: 99, 100, 125, 126
assert(classifyBiomarker('Fasting_Blood_Glucose', 99).status === 'NORMAL', 'FBG 99 mg/dL -> NORMAL');
assert(classifyBiomarker('Fasting_Blood_Glucose', 100).status === 'PREDIABETES', 'FBG 100 mg/dL -> PREDIABETES');
assert(classifyBiomarker('Fasting_Blood_Glucose', 125).status === 'PREDIABETES', 'FBG 125 mg/dL -> PREDIABETES');
assert(classifyBiomarker('Fasting_Blood_Glucose', 126).status === 'ELEVATED', 'FBG 126 mg/dL -> ELEVATED');

// BMI: 24.9, 25.0, 29.9, 30.0
assert(classifyBiomarker('BMI', 24.9).status === 'NORMAL', 'BMI 24.9 kg/m² -> NORMAL');
assert(classifyBiomarker('BMI', 25.0).status === 'OVERWEIGHT', 'BMI 25.0 kg/m² -> OVERWEIGHT');
assert(classifyBiomarker('BMI', 29.9).status === 'OVERWEIGHT', 'BMI 29.9 kg/m² -> OVERWEIGHT');
assert(classifyBiomarker('BMI', 30.0).status === 'OBESITY', 'BMI 30.0 kg/m² -> OBESITY');

// ALT: 7, 44, 56, 57
assert(classifyBiomarker('ALT', 7).status === 'NORMAL', 'ALT 7 U/L -> NORMAL');
assert(classifyBiomarker('ALT', 44).status === 'NORMAL', 'ALT 44 U/L -> NORMAL');
assert(classifyBiomarker('ALT', 56).status === 'NORMAL', 'ALT 56 U/L -> NORMAL');
assert(classifyBiomarker('ALT', 57).status === 'ELEVATED', 'ALT 57 U/L -> ELEVATED');

// Triglycerides: 149, 150, 200
assert(classifyBiomarker('Triglycerides', 149).status === 'NORMAL', 'Triglycerides 149 mg/dL -> NORMAL');
assert(classifyBiomarker('Triglycerides', 150).status === 'ELEVATED', 'Triglycerides 150 mg/dL -> ELEVATED');
assert(classifyBiomarker('Triglycerides', 200).status === 'ELEVATED', 'Triglycerides 200 mg/dL -> ELEVATED');

// BP: 119/79, 120/80, 130/80, 140/90
assert(classifyBiomarker('Blood_Pressure', 119, 79).status === 'NORMAL', 'BP 119/79 mmHg -> NORMAL');
assert(classifyBiomarker('Blood_Pressure', 120, 80).status === 'ELEVATED', 'BP 120/80 mmHg -> ELEVATED');
assert(classifyBiomarker('Blood_Pressure', 130, 80).status === 'ELEVATED', 'BP 130/80 mmHg -> ELEVATED');
assert(classifyBiomarker('Blood_Pressure', 140, 90).status === 'ELEVATED', 'BP 140/90 mmHg -> ELEVATED');

// 3. Missing Value Tests (Requirement 4)
console.log('\n--- 3. Missing Value Tests (Requirement 4) ---');
assert(classifyBiomarker('HbA1c', null).status === 'NOT_PROVIDED', 'HbA1c null -> NOT_PROVIDED (Not Provided)');
assert(classifyBiomarker('HbA1c', undefined).status === 'NOT_PROVIDED', 'HbA1c undefined -> NOT_PROVIDED (Not Provided)');
assert(classifyBiomarker('HbA1c', 'N/A').status === 'NOT_PROVIDED', 'HbA1c "N/A" -> NOT_PROVIDED (Not Provided)');
assert(classifyBiomarker('Fasting_Blood_Glucose', '').status === 'NOT_PROVIDED', 'FBG empty string -> NOT_PROVIDED (Not Provided)');

console.log(`\n===================================`);
console.log(`Total Tests Run: ${passCount + failCount}`);
console.log(`Passed: ${passCount}`);
console.log(`Failed: ${failCount}`);
console.log(`===================================`);

if (failCount > 0) {
  process.exit(1);
} else {
  console.log('ALL UNIT TESTS PASSED SUCCESSFULLY! 🎉');
}
