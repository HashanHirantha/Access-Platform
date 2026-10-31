# AccessGuard භාවිත කරන ආකාරය

මෙය Dialog problem statement එකට ගැළපෙන ක්‍රියාකාරී prototype එකකි. මුල් සේවක සහ application දත්ත කෘත්‍රිම දත්ත වේ. සැබෑ AWS, GitHub හෝ වෙනත් ආයතනික permissions වෙනස් නොකරයි.

## පළමු demo එක

1. App එක විවෘත කර **Access reviews** වෙත යන්න.
2. ඉහළ **Demo persona** තුළ **Hashan Hirantha · Workspace admin** තෝරන්න.
3. `Critical` review එකක් විවෘත කරන්න. උදාහරණයක් ලෙස සේවයෙන් ඉවත් වූ සේවකයෙකුගේ access එකක් තෝරන්න.
4. Evidence සහ recommendation කියවා **Remove access** තෝරන්න. අක්ෂර 8කට වැඩි හේතුවක් ලියා **Record decision** කරන්න.
5. Review එක දැන් **Second approval** තත්ත්වයට යයි. තවම permission එක ඉවත් වී නැත.
6. **Daniel Silva · Security reviewer** persona එක තෝරන්න. **Access reviews → Second approval** තුළ එම review එක විවෘත කරන්න.
7. වෙනම හේතුවක් ලියා **Confirm decision** ලබාදෙන්න.
8. **Remediation** වෙත ගොස් **Review job → Execute & verify** කරන්න.
9. Source record එකෙන් අවසරය ඉවත් කර නැවත කියවා තහවුරු කළ විට **Verified** ලෙස පෙන්වයි.
10. **View evidence** තුළ තහවුරු කිරීමේ සාක්ෂි සහ **Audit trail** තුළ approvals සහ execution සටහන් බලන්න.

## Failure සහ retry පෙන්වීම

Queued job එක විවෘත කර **Simulate connector failure to test safe retry** තෝරා execute කරන්න. Job එක failed වුවත් source permission එක active ලෙසම පවතී. නැවත job එක විවෘත කර simulation එක තෝරා නොගෙන **Retry remediation** කරන්න. සාර්ථක තහවුරු කිරීමෙන් පසුව පමණක් verified වේ.

## ඔබේ CSV දත්ත එකතු කිරීම

**Data sources → Import data** විවෘත කරන්න. **HR identities** හෝ **Access assignments** තෝරා template එක download කරන්න. Sample data භාවිතයෙන්ත් පරීක්ෂා කළ හැකියි.

- Employee ID එක ස්ථිර identity key එකයි.
- Access import එකක employee ID එක දන්නා සේවකයෙකුගේ ID එකක් විය යුතුයි. Owner නොදන්නේ නම් field එක හිස්ව තබන්න.
- Imported application එකකට `Partner CRM` වැනි අලුත් නමක් භාවිත කරන්න. Seeded mock providers overwrite කිරීම ඉඩ නොදේ.
- මුලින් validation සිදුකරයි. වැරදි row එකක් තිබුණොත් අර්ධ import එකක් save නොකරයි.
- එකම file එක නැවත import කළත් duplicates නොසාදයි.
- Import පසුව **Start review → Run risk scan** කරන්න.
- CSV එකේ නොමැති පැරණි records ස්වයංක්‍රීයව delete නොකරයි.

## Roles පරීක්ෂා කිරීම

| Persona | කළ හැකි දේ |
| --- | --- |
| Workspace admin | Import, policies, scans, review decisions සහ demo execution |
| Department reviewer | තමන්ට assign කළ reviews සඳහා තීරණ ලබාදීම |
| Security reviewer | Independent second approvals සහ remediation execution |
| Read-only auditor | Evidence, dashboards සහ reports බැලීම; reports export කිරීම |

තමන්ගේ access තමන්ට approve කළ නොහැකියි. Critical decision එකේ approvals දෙකම එකම පුද්ගලයාට ලබාදිය නොහැකියි. Persona selector එක private demo එක තුළ roles අත්හදා බැලීමට ඇති පහසුකමකි. එය සැබෑ multi-user enterprise login පද්ධතියක් ලෙස ඉදිරිපත් නොකරන්න.

## Presentation එකේ පැහැදිලි කළ යුතු දේ

මෙම prototype එකෙන් data consolidation, explainable risk analysis, approvals, verification සහ audit evidence යන සම්පූර්ණ flow එක පෙන්වයි. Risk scores review priority සඳහාය. මෙහි trained AI model එකක් හෝ live enterprise connector එකක් ඇතුළත් නොවේ. Scans සහ execution ඔබ button එකෙන් ආරම්භ කළ යුතුයි.

Local setup සඳහා README එකේ Node.js 24 සහ pnpm commands අනුගමනය කරන්න. Automated tests වෙනම temporary databases භාවිත කරන නිසා ඔබේ demo records වෙනස් නොවේ.
