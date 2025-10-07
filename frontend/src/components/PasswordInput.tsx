import React, { useState } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  TextFieldProps,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';

interface PasswordInputProps extends TextFieldProps {
  label: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  autoComplete?: string;
  required?: boolean;
  fullWidth?: boolean;
  margin?: 'normal' | 'dense' | 'none';
  disabled?: boolean;
}

const PasswordInput: React.FC<PasswordInputProps> = ({
  label,
  name,
  value,
  onChange,
  autoComplete = 'current-password',
  required = false,
  fullWidth = true,
  margin = 'normal',
  disabled = false,
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleMouseDownPassword = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
  };

  return (
    <TextField
      margin={margin}
      required={required}
      fullWidth={fullWidth}
      name={name}
      label={label}
      type={showPassword ? 'text' : 'password'}
      id={name}
      autoComplete={autoComplete}
      value={value}
      onChange={onChange}
      disabled={disabled}
      {...props}
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            <IconButton
              aria-label="toggle password visibility"
              onClick={handleClickShowPassword}
              onMouseDown={handleMouseDownPassword}
              edge="end"
              size="large"
            >
              {showPassword ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          </InputAdornment>
        ),
      }}
    />
  );
};

export default PasswordInput;