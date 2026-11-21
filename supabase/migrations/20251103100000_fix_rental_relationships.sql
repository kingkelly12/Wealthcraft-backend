-- Drop any existing foreign key constraints
ALTER TABLE public.player_rentals
DROP CONSTRAINT IF EXISTS player_rentals_property_id_fkey;

-- Add the correct foreign key relationship
ALTER TABLE public.player_rentals
ADD CONSTRAINT player_rentals_property_id_fkey
FOREIGN KEY (property_id)
REFERENCES public.rental_properties(id)
ON DELETE CASCADE;

-- Create or replace the view for joined rental data
CREATE OR REPLACE VIEW public.rental_view AS
SELECT 
    pr.*,
    rp.name as property_name,
    rp.property_type,
    rp.location,
    rp.amenities
FROM 
    public.player_rentals pr
    LEFT JOIN public.rental_properties rp ON pr.property_id = rp.id;