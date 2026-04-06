# Lab Supply Management

Εφαρμογή διαχείρισης αναλωσίμων εργαστηρίου — pure Python / Tkinter.

## Εγκατάσταση

```bash
pip install pandas openpyxl matplotlib
```

## Εκκίνηση

```bash
python main.py
```

## Δομή project

```
lab_supply/
│
├── main.py                   ← εδώ τρέχεις
│
├── models/                   ← domain objects (καθαρό Python, χωρίς UI)
│   ├── supply.py             ← Supply dataclass + validation
│   ├── product.py
│   └── analysis.py
│
├── data/                     ← I/O + in-memory store (χωρίς UI)
│   ├── loader.py             ← Excel import/export
│   └── manager.py            ← DataManager (single source of truth)
│
└── ui/                       ← Tkinter (χωρίς business logic)
    ├── theme.py              ← όλα τα χρώματα & fonts εδώ
    ├── widgets.py            ← επαναχρησιμοποιούμενα widgets
    ├── app.py                ← MainApp + sidebar navigation
    ├── dialogs/
    │   └── supply_form.py    ← modal form για add/edit
    └── pages/
        ├── dashboard.py      ← στατιστικά + 2 charts + ειδοποιήσεις λήξης
        ├── supplies.py       ← πλήρης CRUD πίνακας
        ├── products.py       ← catalogue πίνακας (read-only)
        ├── analyses.py       ← catalogue πίνακας (read-only)
        └── blueprints.py     ← snapshots + visual diff
```

## Αρχιτεκτονική

```
models  ←  data  ←  ui
```

- `models/` δεν ξέρει τίποτα για data ή ui
- `data/` γνωρίζει models, ΟΧΙ ui
- `ui/` γνωρίζει data + models, ΟΧΙ αντίθετα
- DataManager ειδοποιεί το UI μέσω callbacks (subscribe pattern)
- Κάθε page ακούει μόνο τον DataManager — δεν μιλάνε μεταξύ τους

## Χρήση

1. Ανοίξτε το app: `python main.py`
2. Πηγαίνετε στην καρτέλα **Αναλώσιμα**
3. Κλικ **↑ Import Excel** — φορτώστε το `2_4.xlsx`
4. Το Dashboard ενημερώνεται αυτόματα
5. Κάντε double-click σε γραμμή για επεξεργασία
6. Για bulk αλλαγές: επιλέξτε πολλές γραμμές → κουμπιά στο κάτω bar
7. Blueprints: αποθηκεύστε snapshot → φορτώστε άλλο Excel → συγκρίνετε

## Προεπιλογές πεδίων «Εφαρμογές Ανάλυσης»

Η εφαρμογή υποστηρίζει πλέον προτεινόμενα defaults για το πεδίο
**Εφαρμογές Ανάλυσης** στα dialogs **Νέο Προϊόν** και **Νέο Αναλώσιμο**.

### Πώς υπολογίζεται το default

Για τον επιλεγμένο **Τύπο**:

1. Αν υπάρχουν ήδη προϊόντα ίδιου τύπου, χρησιμοποιείται η πιο συχνή τιμή
   του `analysis_applications`.
2. Αν δεν υπάρχει ιστορικό για τον τύπο, γίνεται fallback σε λίστα με τα ονόματα
   από την καρτέλα **Αναλύσεις** (comma-separated).

### Συμπεριφορά στο UI

- Το default συμπληρώνεται αυτόματα στο άνοιγμα νέας φόρμας.
- Αν αλλάξει ο τύπος, το default ενημερώνεται μόνο όταν το πεδίο δεν έχει
  χειροκίνητα τροποποιηθεί από τον χρήστη.
- Σε edit υπάρχουσας εγγραφής, διατηρούνται οι υπάρχουσες τιμές.

## Quick actions για κατάσταση αναλωσίμων

Στο κάτω action bar της καρτέλας **Αναλώσιμα**, όταν υπάρχουν επιλεγμένες γραμμές,
υπάρχουν γρήγορα κουμπιά:

- **Ανοιχτό → Τελειωμένο**
- **Κλειστό → Ανοιχτό**

Τα quick actions εφαρμόζονται μόνο στα επιλεγμένα items που όντως βρίσκονται
στην source κατάσταση. Αν δεν υπάρχει καμία αντιστοιχία, εμφανίζεται ενημερωτικό
μήνυμα χωρίς να γίνει αλλαγή.
