"""Inter-rater reliability calculation."""
from typing import Dict, List, Any
from database.queries import ReviewDatabase

try:
    from sklearn.metrics import cohen_kappa_score
except ImportError:
    cohen_kappa_score = None

class ReliabilityCalculator:
    """Calculate inter-rater reliability metrics."""

    def __init__(self, review_db: ReviewDatabase):
        """
        Initialize reliability calculator.

        Args:
            review_db: ReviewDatabase instance
        """
        self.review_db = review_db

    def calculate_screening_kappa(
        self,
        review_id: int,
        stage: str
    ) -> Dict[str, Any]:
        """
        Calculate Cohen's kappa for screening decisions.

        Args:
            review_id: Review ID
            stage: Screening stage

        Returns:
            Dictionary with kappa, interpretation, agreements
        """
        if cohen_kappa_score is None:
            raise ImportError("scikit-learn required for kappa calculation")

        # Get all papers in review
        papers = self.review_db.get_review_papers(review_id)

        # Find papers screened by exactly 2 reviewers
        agreements = []
        for paper_id in papers:
            decisions = self.review_db.get_screening_decisions(
                review_id,
                paper_id,
                stage
            )

            if len(decisions) == 2:
                agreements.append({
                    'paper_id': paper_id,
                    'reviewer1': decisions[0]['reviewer_id'],
                    'reviewer2': decisions[1]['reviewer_id'],
                    'decision1': decisions[0]['decision'],
                    'decision2': decisions[1]['decision'],
                    'agree': decisions[0]['decision'] == decisions[1]['decision']
                })

        if not agreements:
            return {'error': 'No dual-screened papers found'}

        # Calculate Cohen's kappa
        labels1 = [a['decision1'] for a in agreements]
        labels2 = [a['decision2'] for a in agreements]
        kappa = cohen_kappa_score(labels1, labels2)

        # Interpret (Landis & Koch)
        if kappa < 0:
            interpretation = 'Poor'
        elif kappa < 0.20:
            interpretation = 'Slight'
        elif kappa < 0.40:
            interpretation = 'Fair'
        elif kappa < 0.60:
            interpretation = 'Moderate'
        elif kappa < 0.80:
            interpretation = 'Substantial'
        else:
            interpretation = 'Almost Perfect'

        # Calculate percent agreement
        agree_count = sum(a['agree'] for a in agreements)
        percent_agreement = (agree_count / len(agreements)) * 100

        return {
            'kappa': kappa,
            'interpretation': interpretation,
            'total_papers': len(agreements),
            'agreements': agree_count,
            'percent_agreement': percent_agreement,
            'disagreements': [a for a in agreements if not a['agree']]
        }

    def _interpret_kappa(self, kappa: float) -> str:
        """Interpret kappa value using Landis & Koch scale."""
        if kappa < 0:
            return 'Poor'
        elif kappa < 0.20:
            return 'Slight'
        elif kappa < 0.40:
            return 'Fair'
        elif kappa < 0.60:
            return 'Moderate'
        elif kappa < 0.80:
            return 'Substantial'
        else:
            return 'Almost Perfect'
