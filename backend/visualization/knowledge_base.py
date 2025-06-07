import modal

gitingest_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("curl", "git")
    .pip_install("uv")
    .run_commands("uv pip install --system --compile-bytecode gitingest")
)

app = modal.App(name="update-recharts-docs", image=gitingest_image)

volume = modal.Volume.from_name("knowledge-base", create_if_missing=True)

@app.function(schedule=modal.Cron(cron_string="0 4 */3 * *", timezone="Europe/Berlin"), 
              volumes={"/data": volume})
def update_recharts_docs(github_url: str = "https://github.com/recharts/recharts/tree/3.x/storybook"):
    """
    Fetches and stores Recharts documentation in the knowledge base for the visualization agent.
    
    Args:
        github_url (str): URL to the GitHub repository containing the docs.
                       Defaults to the recharts storybook.
    
    Raises:
        RuntimeError: If there's an error during the documentation fetch or save process.
    """
    import asyncio
    import datetime
    import logging
    import os
    from gitingest import ingest_async
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    
    logger = logging.getLogger(__name__)
    
    OUTPUT_DIR = "/data/recharts_docs"
    logger.info(f"📁 Output directory: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    logger.info(f"🕒 Current timestamp: {timestamp}")

    output_file = os.path.join(OUTPUT_DIR, f"recharts_{timestamp}.txt")
    logger.info(f"💾 Output file: {output_file}")
    
    try:
        logger.info("⬇️  Fetching updated docs...")
        asyncio.run(
            ingest_async(
                source=github_url,
                max_file_size=100 * 1024 * 1024,  # 100MB
                branch="3.x",
                output=output_file
            )
        )
        logger.info("✅ Successfully fetched and saved documentation")
        volume.commit()
        logger.info("💾 Volume changes committed successfully")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise RuntimeError(f"Failed to fetch or save documentation: {str(e)}")

if __name__ == "__main__":
    app.deploy()
