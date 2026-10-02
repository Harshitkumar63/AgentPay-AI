"""AI A/B Testing & Experimentation Service (Part 24).

Tracks multi-variant pricing experiments, conversion lifts, and statistical recommendations.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.experiment import Experiment, ExperimentVariant


def init_default_experiments(db: Session, merchant_id: str = "merchant_001"):
    """Seed sample active A/B pricing experiment if none exist."""
    existing = db.query(Experiment).filter(Experiment.merchant_id == merchant_id).first()
    if not existing:
        exp = Experiment(
            merchant_id=merchant_id,
            product_id="prod_001",
            name="ProRunner X1 Price Elasticity Experiment",
            hypothesis="Pricing at ₹2,299 instead of ₹2,499 will drive +15% conversion and increase overall net revenue.",
            status="RUNNING",
            ai_recommendation="Variant B demonstrates a +14.2% conversion lift and +7.8% higher total revenue. Recommend standardizing on Variant B.",
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        v_a = ExperimentVariant(
            experiment_id=exp.id,
            name="Variant A (Control)",
            price=2499.0,
            views=320,
            orders=24,
            revenue=59976.0,
        )
        v_b = ExperimentVariant(
            experiment_id=exp.id,
            name="Variant B (Discounted)",
            price=2299.0,
            views=315,
            orders=34,
            revenue=78166.0,
        )
        db.add_all([v_a, v_b])
        db.commit()


def get_experiments(db: Session, merchant_id: str = "merchant_001") -> List[Experiment]:
    """Retrieve all A/B experiments for merchant."""
    init_default_experiments(db, merchant_id)
    return db.query(Experiment).filter(Experiment.merchant_id == merchant_id).all()


def create_experiment(
    db: Session,
    product_id: str,
    name: str,
    hypothesis: str,
    variant_a_price: float,
    variant_b_price: float,
    merchant_id: str = "merchant_001",
) -> Experiment:
    """Create a new pricing experiment with two variants."""
    exp = Experiment(
        merchant_id=merchant_id,
        product_id=product_id,
        name=name,
        hypothesis=hypothesis,
        status="RUNNING",
        ai_recommendation="Experiment initiated. Awaiting initial traffic to compute statistical significance.",
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    v_a = ExperimentVariant(
        experiment_id=exp.id,
        name="Variant A (Baseline)",
        price=variant_a_price,
        views=1,
        orders=0,
        revenue=0.0,
    )
    v_b = ExperimentVariant(
        experiment_id=exp.id,
        name="Variant B (Test)",
        price=variant_b_price,
        views=1,
        orders=0,
        revenue=0.0,
    )
    db.add_all([v_a, v_b])
    db.commit()
    db.refresh(exp)

    return exp
