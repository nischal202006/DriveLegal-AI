"""
Challan Calculator Engine â€” DriveLegal.ai
Intelligent fine calculation with state overrides and vehicle modifiers.
Covers all 66+ violations from the Motor Vehicles (Amendment) Act, 2019.
"""


class ChallanCalculator:
    """Calculates traffic violation fines with location and vehicle awareness."""

    # Vehicle type modifiers â€“ heavier vehicles attract higher fines
    VEHICLE_MODIFIERS = {
        'two_wheeler': 0.75,
        'auto_rickshaw': 0.85,
        'car': 1.0,
        'taxi': 1.1,
        'bus': 1.5,
        'truck': 1.5,
        'commercial': 1.3,
        'e_rickshaw': 0.8,
    }

    def __init__(self, db=None):
        self.db = db

    # â”€â”€ Single violation â”€â”€
    def calculate(self, violation_key, vehicle_type='car', state_key=None,
                  is_repeat=False, extra_passengers=0, extra_tonnes=0):
        """
        Calculate fine for a single violation.
        Returns dict with fine breakdown, section reference, and penalties.
        """
        if not self.db:
            return {'error': 'Database not loaded'}

        violation = self.db.get_violation(violation_key)
        if not violation:
            return {'error': f'Unknown violation: {violation_key}'}

        # â”€â”€ Base fine â”€â”€
        fine = violation.get('fine', 0)
        if isinstance(fine, dict):
            fine = fine.get('first', fine.get('min', 0))

        # â”€â”€ Repeat-offense multiplier â”€â”€
        if is_repeat:
            repeat_fine = violation.get('fine', {})
            if isinstance(repeat_fine, dict) and 'repeat' in repeat_fine:
                fine = repeat_fine['repeat']
            else:
                fine = int(fine * 2)

        # â”€â”€ Vehicle modifier â”€â”€
        modifier = self.VEHICLE_MODIFIERS.get(vehicle_type, 1.0)
        fine = int(fine * modifier)

        # â”€â”€ State override â”€â”€
        state_fine = None
        state_label = 'National (MV Act 2019)'
        if state_key and self.db:
            override = self.db.get_state_override(state_key, violation_key)
            if override:
                state_fine = override.get('fine', fine)
                if isinstance(state_fine, dict):
                    state_fine = state_fine.get('repeat' if is_repeat else 'first',
                                                state_fine.get('min', fine))
                state_fine = int(state_fine * modifier)
                state_label = self.db.get_state_name(state_key) or state_key

        # â”€â”€ Overloading surcharge â”€â”€
        overload_surcharge = 0
        if extra_passengers > 0 and violation_key == 'overloading_passengers':
            overload_surcharge = extra_passengers * 1000 * modifier
        if extra_tonnes > 0 and violation_key == 'overloading_goods':
            overload_surcharge = extra_tonnes * 2000 * modifier

        total_fine = (state_fine if state_fine is not None else fine) + overload_surcharge

        # â”€â”€ Imprisonment check â”€â”€
        imprisonment = violation.get('imprisonment', None)

        return {
            'violation_key': violation_key,
            'violation_name': violation.get('name', violation_key),
            'section': violation.get('section', 'â€”'),
            'national_fine': fine,
            'state_fine': state_fine,
            'state_label': state_label,
            'vehicle_type': vehicle_type,
            'vehicle_modifier': modifier,
            'is_repeat': is_repeat,
            'overload_surcharge': int(overload_surcharge),
            'total_fine': int(total_fine),
            'imprisonment': imprisonment,
            'points': violation.get('points', 0),
        }

    # â”€â”€ Multiple violations â”€â”€
    
