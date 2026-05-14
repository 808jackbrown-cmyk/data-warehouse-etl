import logging, sys, time
import sqlalchemy as sa
from extract import extract_all, load_config
from transform import transform_all
from load import load_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("pipeline.log")])
logger = logging.getLogger("pipeline")

def run():
    start = time.time()
    logger.info("="*50)
    logger.info("PIPELINE START")
    logger.info("="*50)
    config = load_config("config/config.yaml")
    engine = sa.create_engine("sqlite:///data/sample.db")

    logger.info("STEP 1/3 — EXTRACT")
    raw = extract_all(config)

    logger.info("STEP 2/3 — TRANSFORM")
    transformed = transform_all(raw)

    logger.info("STEP 3/3 — LOAD")
    load_all(transformed, engine)

    logger.info(f"PIPELINE COMPLETE in {time.time()-start:.1f}s")
    logger.info("="*50)

if __name__ == "__main__":
    run()
