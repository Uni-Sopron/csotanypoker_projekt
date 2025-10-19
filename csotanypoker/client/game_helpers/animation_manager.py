class AnimationManager:
    def __init__(self):
        self._flip_progress = {}
    
    def get_flip_data(self, card_key, target_card):
        if card_key not in self._flip_progress:
            self._flip_progress[card_key] = {
                'previous_card': None,
                'current_card': target_card,
                'progress': 1.0,
                'is_animating': False
            }
        
        flip_data = self._flip_progress[card_key]

        if flip_data['current_card'] != target_card:
            if flip_data['current_card'] == 'card_back' and target_card != 'card_back':
                flip_data['progress'] = 0.0
                flip_data['previous_card'] = flip_data['current_card']
                flip_data['current_card'] = target_card
                flip_data['is_animating'] = True
            else:
                flip_data['previous_card'] = flip_data['current_card']
                flip_data['current_card'] = target_card
                flip_data['progress'] = 1.0
                flip_data['is_animating'] = False
        
        if flip_data['is_animating']:
            if flip_data['progress'] < 1.0:
                flip_data['progress'] += 0.15
                if flip_data['progress'] >= 1.0:
                    flip_data['progress'] = 1.0
                    flip_data['is_animating'] = False
        
        return flip_data
    
    def reset(self):
        self._flip_progress.clear()
