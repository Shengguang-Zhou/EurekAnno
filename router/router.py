"""
#   © 2024 EurekAILab. All rights reserved.
#   No part of this publication may be reproduced, distributed,
#   or transmitted in any form or by any means, including photocopying, recording,
#   or other electronic or mechanical methods, without the prior written permission of the publisher,
#   except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
"""

from fastapi import APIRouter
from app.api.yoloe import router as yoloe_router

# Create a "master" API router
api_router = APIRouter()

# Include the YOLOE router, giving it a prefix and tags
api_router.include_router(yoloe_router, prefix="/yoloe", tags=["YOLOE"])

