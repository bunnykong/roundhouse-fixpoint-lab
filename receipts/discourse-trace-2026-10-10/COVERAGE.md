# All 28 selected reads

Condition: `sound-traces-20261010-c210f226`. P, E and I are the separate runtime settings
declared in [README.md](README.md). Each cell is `main accepted/rejected; S3 accepted/rejected`.
Zero observations remain in the denominator. All reads belong to instance-side
`Jobs::Base::JobInstrumenter` in `app/jobs/base.rb`; the [slot map](slots.json) and
[per-slot decisions](per-slot-decisions.json) retain exact byte spans and trace-line references.

| Method and line:column | P | E | I |
| --- | --- | --- | --- |
| initialize 53:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| initialize 54:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| initialize 55:11 | 1/0; 0/1 | 3/0; 0/3 | 1/0; 0/1 |
| initialize 56:11 | 1/0; 0/1 | 3/0; 0/3 | 1/0; 0/1 |
| initialize 57:11 | 1/0; 0/1 | 3/0; 0/3 | 1/0; 0/1 |
| initialize 58:11 | 1/0; 0/1 | 3/0; 0/3 | 1/0; 0/1 |
| initialize 59:11 | 1/0; 0/1 | 3/0; 0/3 | 1/0; 0/1 |
| initialize 62:13 | 0/0; 0/0 | 0/0; 0/0 | 1/0; 0/1 |
| initialize 66:11 | 1/0; 0/1 | 3/0; 0/3 | 1/0; 0/1 |
| initialize 75:11 | 1/0; 0/1 | 3/0; 0/3 | 1/0; 0/1 |
| stop 87:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 88:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 89:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 90:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 91:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 92:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 93:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 94:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 95:11 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 95:33 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 95:62 | 1/0; 1/0 | 3/0; 3/0 | 1/0; 1/0 |
| stop 98:13 | 0/0; 0/0 | 3/0; 3/0 | 0/0; 0/0 |
| stop 99:13 | 0/0; 0/0 | 3/0; 3/0 | 0/0; 0/0 |
| stop 101:13 | 1/0; 1/0 | 0/0; 0/0 | 1/0; 1/0 |
| write_to_log 144:9 | 1/0; 1/0 | 3/0; 3/0 | 2/0; 2/0 |
| write_to_log 145:9 | 0/0; 0/0 | 0/0; 0/0 | 0/0; 0/0 |
| write_to_log 145:49 | 1/0; 1/0 | 3/0; 3/0 | 2/0; 2/0 |
| write_to_log 146:31 | 1/0; 1/0 | 3/0; 3/0 | 2/0; 2/0 |

The only read unobserved across all three settings is `write_to_log` at 145:9,
byte span 4187–4192. The combined coverage is 27/28, with 127 observations:
main 127 accepted / 0 rejected; S3 91 accepted / 36 rejected. Every acceptance is
qualified by an uncertain or unsupported type component.
