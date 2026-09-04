# RecoverAI Dataset EDA Report

Generated with dataset seed 42.

## Integrity checks

| check                       | result                                                                                                              | interpretation                                               |
|:----------------------------|:--------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------|
| Customer rows               | 4,000                                                                                                               | Expected 4,000.                                              |
| Recovery rows               | 20,000                                                                                                              | Expected 20,000.                                             |
| Duplicate payment IDs       | 0                                                                                                                   | Should be 0.                                                 |
| Missing values              | 0                                                                                                                   | Should be 0.                                                 |
| Recoverable rate            | 59.7%                                                                                                               | Healthy target: neither extremely rare nor nearly universal. |
| Test set size               | 3,000                                                                                                               | Expected 3,000.                                              |
| Post-outcome / label fields | recovery_probability_ground_truth, recoverable, optimal_action, recovered, amount_recovered, baseline_action, split | These must be excluded from model features.                  |

## Numeric feature correlation with recoverable

|                         |   correlation |
|:------------------------|--------------:|
| customer_success_rate   |     0.149173  |
| customer_total_payments |     0.0647662 |
| customer_lifetime_value |     0.0613433 |
| average_payment         |     0.0516019 |
| amount                  |     0.0439257 |
| days_since_last_success |    -0.0111889 |
| customer_failure_rate   |    -0.149173  |
| attempt_number          |    -0.150488  |

## Failure reason summary

| failure_reason         |   cases | recoverable_rate   | avg_amount   | recovered_amount   |
|:-----------------------|--------:|:-------------------|:-------------|:-------------------|
| network_error          |    3934 | 84.7%              | ₹12,416      | ₹39,966,745        |
| insufficient_funds     |    5390 | 70.5%              | ₹12,810      | ₹46,196,276        |
| authentication_failure |    2412 | 55.8%              | ₹13,086      | ₹14,125,772        |
| bank_decline           |    3282 | 52.0%              | ₹12,767      | ₹18,430,490        |
| expired_card           |    2764 | 42.6%              | ₹11,928      | ₹16,943,266        |
| payment_method_invalid |    2218 | 25.9%              | ₹13,098      | ₹10,329,184        |

## Attempt number summary

|   attempt_number |   cases | recoverable_rate   |   avg_recovery_probability |
|-----------------:|--------:|:-------------------|---------------------------:|
|                1 |   11634 | 65.4%              |                      0.648 |
|                2 |    6162 | 54.3%              |                      0.546 |
|                3 |    1790 | 46.6%              |                      0.452 |
|                4 |     362 | 35.1%              |                      0.357 |
|                5 |      52 | 40.4%              |                      0.262 |

## Customer segment summary

| segment    |   cases | recoverable_rate   | avg_amount   |
|:-----------|--------:|:-------------------|:-------------|
| at_risk    |    1986 | 40.4%              | ₹10,936      |
| high_value |    3514 | 69.9%              | ₹37,225      |
| new        |    4161 | 56.2%              | ₹4,615       |
| regular    |   10339 | 61.3%              | ₹7,897       |

## Leakage controls

The following columns are post-outcome/label-generation fields and are excluded from model features: recovery_probability_ground_truth, recoverable, optimal_action, recovered, amount_recovered, baseline_action, split.
