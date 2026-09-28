/**
 * Local icon assets (avoid mixing icon libraries — master prompt §34).
 * These are thin wrappers around MUI icons so the design-system has ONE
 * coherent icon source. Add more here as the system grows.
 */
import { SvgIcon, SvgIconProps } from '@mui/material';
import { Box } from '@mui/material';
import ShieldCheck from '@mui/icons-material/Shield';
import History from '@mui/icons-material/History';
import MedicalServices from '@mui/icons-material/MedicalServices';
import HelpOutline from '@mui/icons-material/HelpOutline';
import MenuIconBase from '@mui/icons-material/Menu';
import Close from '@mui/icons-material/Close';
import ArrowBack from '@mui/icons-material/ArrowBack';
import ErrorOutline from '@mui/icons-material/ErrorOutline';
import InfoOutline from '@mui/icons-material/InfoOutlined';
import CheckCircle from '@mui/icons-material/CheckCircle';
import WarningAmber from '@mui/icons-material/WarningAmber';

export const ShieldCheckIcon: React.FC<SvgIconProps> = (p) => <ShieldCheck {...p} />;
export const HistoryIcon: React.FC<SvgIconProps> = (p) => <History {...p} />;
export const MedicalIcon: React.FC<SvgIconProps> = (p) => <MedicalServices {...p} />;
export const HelpIcon: React.FC<SvgIconProps> = (p) => <HelpOutline {...p} />;
export const MenuIcon: React.FC<SvgIconProps> = (p) => <MenuIconBase {...p} />;
export const CloseIcon: React.FC<SvgIconProps> = (p) => <Close {...p} />;
export const ArrowBackIcon: React.FC<SvgIconProps> = (p) => <ArrowBack {...p} />;
export const ErrorOutlineIcon: React.FC<SvgIconProps> = (p) => <ErrorOutline {...p} />;
export const InfoOutlineIcon: React.FC<SvgIconProps> = (p) => <InfoOutline {...p} />;
export const CheckCircleIcon: React.FC<SvgIconProps> = (p) => <CheckCircle {...p} />;
export const WarningIcon: React.FC<SvgIconProps> = (p) => <WarningAmber {...p} />;

export const Logo: React.FC<{ sx?: object; width?: number | string; height?: number | string }> = ({
  sx,
  width = 40,
  height = 40,
}) => (
  <Box
    component="img"
    src="/images/logo.jpeg"
    alt="DEDAN Health Logo"
    sx={{
      width,
      height,
      objectFit: 'contain',
      flexShrink: 0,
      ...sx,
    }}
  />
);
